import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import os

# SQL Server bağlantısı
engine = create_engine('mssql+pyodbc://usesen:usesen@DESKTOP-6QR83E3\\UGURMSSQL/FSM_Tickets?driver=SQL+Server')

# SQL sorgusu - Tüm bölgeler için
query = """
SELECT 
    DATEPART(month, Olusturma_Tarihi) as Ay,
    Bolge,
    Teknisyen,
    COUNT(*) as Ticket_Sayisi,
    COUNT(DISTINCT CAST(Olusturma_Tarihi as DATE)) as Is_Gunu_Sayisi,
    COUNT(*) / COUNT(DISTINCT CAST(Olusturma_Tarihi as DATE)) as Gunluk_Ortalama
FROM Tickets
WHERE 
    Olusturma_Tarihi >= '2024-01-01' 
    AND Olusturma_Tarihi < '2024-04-01'
    AND DATEPART(dw, Olusturma_Tarihi) NOT IN (1, 7)  -- Hafta sonu hariç
GROUP BY 
    DATEPART(month, Olusturma_Tarihi),
    Bolge,
    Teknisyen
ORDER BY 
    Bolge, Ay, Teknisyen
"""

# Veriyi çek
df = pd.read_sql(query, engine)

# İzmir'in mevsimsel faktörleri
izmir_factors = {
    4: 1.00,  # Normal
    5: 1.05,  # Bahar
    6: 1.15,  # Yaz başlangıcı
    7: 1.30,  # Yaz yoğun
    8: 1.30,  # Yaz yoğun
    9: 1.10,  # Azalma başlar
    10: 1.00, # Normal
    11: 1.00, # Normal
    12: 1.00  # Normal
}

# 2024 ayları için iş günü sayıları
working_days = {
    4: 22,  # Nisan
    5: 22,  # Mayıs
    6: 20,  # Haziran
    7: 23,  # Temmuz
    8: 22,  # Ağustos
    9: 21,  # Eylül
    10: 22, # Ekim
    11: 21, # Kasım
    12: 22  # Aralık
}

# Bölge bazlı mevsimsel faktörler
seasonal_factors = {
    'İzmir': izmir_factors,
    'Antalya': {
        4: 1.00,  # Normal
        5: 1.10,  # Turizm başlangıcı
        6: 1.25,  # Yaz başlangıcı
        7: 1.35,  # Yaz zirvesi
        8: 1.35,  # Yaz zirvesi devam
        9: 1.20,  # Hala yoğun
        10: 1.05, # Azalma başlar
        11: 1.00, # Normal
        12: 1.00  # Normal
    },
    # Diğer bölgeler için faktörler eklenebilir
    'Default': {4: 1.00, 5: 1.00, 6: 1.00, 7: 1.00, 8: 1.00, 9: 1.00, 10: 1.00, 11: 1.00, 12: 1.00}
}

# Teknisyen seviyelerine göre iş yükü dağılımı
teknisyen_seviye_katsayi = {
    'Senior': 1.3,    # Özlem Demir
    'Mid-Level': 1.1, # Tolga Kaya
    'Junior': 0.8     # Pınar Yılmaz
}

def get_teknisyen_seviyesi(teknisyen_adi):
    # Varsayılan olarak Mid-Level döndür
    # Daha sonra bu fonksiyonu gerçek iş kurallarına göre güncelleyebilirsiniz
    return 'Mid-Level'

# Teknisyen bazlı tahminleme
def calculate_predictions(bolge_df, bolge):
    # İlk 3 ayın ortalamasını al
    teknisyen_ortalamalar = bolge_df.groupby('Teknisyen')['Gunluk_Ortalama'].mean()
    
    # Her teknisyenin toplam içindeki payını hesapla
    toplam_ortalama = teknisyen_ortalamalar.sum()
    teknisyen_oranlar = teknisyen_ortalamalar / toplam_ortalama
    
    # Tahminleri hesapla
    tahminler = []
    
    # Bölgenin mevsimsel faktörlerini al
    bolge_factors = seasonal_factors.get(bolge, seasonal_factors['Default'])
    
    # İlk 3 ay gerçek veriler
    for teknisyen in bolge_df['Teknisyen'].unique():
        row = {'Teknisyen': teknisyen}
        for ay in range(1, 4):
            ay_verisi = bolge_df[(bolge_df['Teknisyen'] == teknisyen) & (bolge_df['Ay'] == ay)]
            row[f'2024-{ay:02d}'] = 0 if ay_verisi.empty else ay_verisi['Ticket_Sayisi'].iloc[0]
        tahminler.append(row)
    
    # Gelecek aylar için tahmin
    for teknisyen in bolge_df['Teknisyen'].unique():
        oran = teknisyen_oranlar[teknisyen]
        for ay in range(4, 13):
            seviye = teknisyen_seviye_katsayi[get_teknisyen_seviyesi(teknisyen)]
            base_tickets = int(teknisyen_ortalamalar[teknisyen] * working_days[ay] * seviye)
            seasonal_tickets = int(base_tickets * bolge_factors[ay])
            
            for t in tahminler:
                if t['Teknisyen'] == teknisyen:
                    t[f'2024-{ay:02d}'] = seasonal_tickets
                    break
    
    return pd.DataFrame(tahminler)

# Excel'e aktar
try:
    with pd.ExcelWriter('bolgesel_teknisyen_tahminleri_2024.xlsx', engine='openpyxl') as writer:
        for bolge in df['Bolge'].unique():
            bolge_df = df[df['Bolge'] == bolge]
            predictions_df = calculate_predictions(bolge_df, bolge)
            
            # Bölge toplamlarını hesapla
            bolge_totals = predictions_df.drop('Teknisyen', axis=1).sum()
            bolge_summary_df = pd.DataFrame({
                'Teknisyen': [f'{bolge} TOPLAM'],
                **{f'2024-{i:02d}': [bolge_totals[f'2024-{i:02d}']] for i in range(1, 13)}
            })
            
            # Boş satır ekle
            empty_row = pd.DataFrame({'Teknisyen': [''], **{f'2024-{i:02d}': [''] for i in range(1, 13)}})
            
            # Yıllık toplam sütunu ekle
            predictions_df['TOPLAM'] = predictions_df.iloc[:, 1:].sum(axis=1)
            bolge_summary_df['TOPLAM'] = bolge_summary_df.iloc[:, 1:].sum(axis=1)
            
            # Tüm verileri birleştir
            final_df = pd.concat([
                bolge_summary_df,
                empty_row,
                predictions_df,
                pd.DataFrame({'Teknisyen': ['GENEL TOPLAM'], **{f'2024-{i:02d}': [bolge_totals[f'2024-{i:02d}']] for i in range(1, 13)}, 'TOPLAM': [bolge_totals.sum()]})
            ], ignore_index=True)
            
            # Tek sayfaya yaz
            final_df.to_excel(writer, sheet_name=f'{bolge}', index=False)

except Exception as e:
    print(f"Hata oluştu: {e}")

print("Çalışma tamamlandı.")