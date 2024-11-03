import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
import skl2onnx
import onnxruntime as rt
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
from sklearn.model_selection import cross_val_score
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, mean_absolute_percentage_error
import math
from sklearn.linear_model import LinearRegression
import seaborn as sns
import os

# Matplotlib backend'i kontrol et ve ayarla
import matplotlib
print("Backend:", matplotlib.get_backend())
matplotlib.use('TkAgg')  # veya 'Agg' ya da 'Qt5Agg'

# SQL Server bağlantısı
engine = create_engine('mssql+pyodbc://usesen:usesen@DESKTOP-6QR83E3\\UGURMSSQL/FSM_Tickets?driver=SQL+Server')

# SQL sorgusu - Bölge bilgisini de alalım
query = """
SELECT 
    DATEPART(month, Olusturma_Tarihi) as Ay,
    Bolge,  -- Bölge bilgisini ekledik
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
    Bolge  -- Bölgeye göre de grupla
ORDER BY 
    Ay, Bolge
"""

# Veriyi çek ve analiz et
df = pd.read_sql(query, engine)
print("Mevcut Veriler:")
print(df)

# Günlük ortalama ticket sayısını hesapla
df['Gunluk_Ort'] = df['Ticket_Sayisi'] / df['Is_Gunu_Sayisi']
avg_daily_tickets = df['Gunluk_Ort'].mean()
std_daily_tickets = df['Gunluk_Ort'].std()  # Günlük standart sapma

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
seasonal_regional_factors = {
    'Ankara': {
        4: 1.05,  # Bahar dönemi
        5: 1.10,  # Bahar dönemi
        6: 0.95,  # Yaz başlangıcı
        7: 0.80,  # Yaz tatili
        8: 0.75,  # Yaz tatili
        9: 1.15,  # Okullar açılıyor
        10: 1.05, # Normal
        11: 1.00, # Normal
        12: 0.90  # Yılsonu
    },
    'İstanbul-Avrupa': {
        4: 1.10,  # Bahar
        5: 1.15,  # Yoğun dönem
        6: 0.95,  # Normal
        7: 0.85,  # Yaz düşüşü
        8: 0.80,  # Yaz düşüşü
        9: 1.20,  # En yoğun
        10: 1.10, # Yoğun
        11: 1.05, # Normal
        12: 0.95  # Yılsonu
    },
    'İstanbul-Anadolu': {
        4: 1.10,  # Bahar
        5: 1.15,  # Yoğun dönem
        6: 0.95,  # Normal
        7: 0.85,  # Yaz düşüşü
        8: 0.80,  # Yaz düşüşü
        9: 1.20,  # En yoğun
        10: 1.10, # Yoğun
        11: 1.05, # Normal
        12: 0.95  # Yılsonu
    },
    'İzmir': {
        4: 1.05,  # Bahar
        5: 1.10,  # Bahar
        6: 1.15,  # Yaz başlangıcı
        7: 1.20,  # Yaz
        8: 1.20,  # Yaz
        9: 1.10,  # Normal üstü
        10: 1.00, # Normal
        11: 0.95, # Normal
        12: 0.90  # Yılsonu
    },
    'Bursa': {
        4: 1.05,  # Bahar
        5: 1.10,  # Bahar
        6: 1.00,  # Normal
        7: 0.85,  # Yaz düşüşü
        8: 0.80,  # Yaz düşüşü
        9: 1.15,  # Yoğun
        10: 1.05, # Normal
        11: 1.00, # Normal
        12: 0.95  # Normal
    },
    'Antalya': {
        4: 1.15,  # Turizm
        5: 1.20,  # Turizm
        6: 1.25,  # Yaz başlangıcı
        7: 1.30,  # Yaz
        8: 1.30,  # Yaz
        9: 1.20,  # Turizm devam
        10: 1.10, # Turizm azalıyor
        11: 1.05, # Normal
        12: 1.15  # Kış turizmi
    }
}
print("\nGünlük Ortalama Ticket:", f"{avg_daily_tickets:.0f}")
print("Günlük Standart Sapma:", f"±{std_daily_tickets:.0f}")
print("\nTahmin Edilen Aylık Ticket Sayıları:")
for month in range(4, 13):
    monthly_pred = int(avg_daily_tickets * working_days[month])
    monthly_std = int(std_daily_tickets * working_days[month])  # Aylık standart sapma
    print(f"2024-{month:02d}: {monthly_pred} ticket (±{monthly_std})")


# Aylık ortalama ticket sayısı üzerinden tahmin
df['Aylik_Ortalama'] = df['Ticket_Sayisi'] / df['Is_Gunu_Sayisi']
aylik_ortalamalar = df.set_index('Ay')['Aylik_Ortalama']

print("\nAylık Tahmin Edilen Ticket Sayıları (Mevcut Ortalama Üzerinden):")
for month in range(4, 13):
    if month in aylik_ortalamalar.index:
        monthly_pred = int(aylik_ortalamalar[month] * working_days[month])
    else:
        monthly_pred = int(aylik_ortalamalar.mean() * working_days[month])  # Bilinmeyen aylar için ortalama kullanılıyor
    print(f"2024-{month:02d}: {monthly_pred} ticket")

# Bölge ve aya göre mevsimsel faktörler
seasonal_regional_factors = {
    'Ankara': {
        4: 1.05,  # Bahar dönemi
        5: 1.10,  # Bahar dönemi
        6: 0.95,  # Yaz başlangıcı
        7: 0.80,  # Yaz tatili
        8: 0.75,  # Yaz tatili
        9: 1.15,  # Okullar açılıyor
        10: 1.05, # Normal
        11: 1.00, # Normal
        12: 0.90  # Yılsonu
    },
    'İstanbul-Avrupa': {
        4: 1.10,  # Bahar
        5: 1.15,  # Yoğun dönem
        6: 0.95,  # Normal
        7: 0.85,  # Yaz düşüşü
        8: 0.80,  # Yaz düşüşü
        9: 1.20,  # En yoğun
        10: 1.10, # Yoğun
        11: 1.05, # Normal
        12: 0.95  # Yılsonu
    },
    'İstanbul-Anadolu': {
        4: 1.10,  # Bahar
        5: 1.15,  # Yoğun dönem
        6: 0.95,  # Normal
        7: 0.85,  # Yaz düşüşü
        8: 0.80,  # Yaz düşüşü
        9: 1.20,  # En yoğun
        10: 1.10, # Yoğun
        11: 1.05, # Normal
        12: 0.95  # Yılsonu
    },
    'İzmir': {
        4: 1.05,  # Bahar
        5: 1.10,  # Bahar
        6: 1.15,  # Yaz başlangıcı
        7: 1.20,  # Yaz
        8: 1.20,  # Yaz
        9: 1.10,  # Normal üstü
        10: 1.00, # Normal
        11: 0.95, # Normal
        12: 0.90  # Yılsonu
    },
    'Bursa': {
        4: 1.05,  # Bahar
        5: 1.10,  # Bahar
        6: 1.00,  # Normal
        7: 0.85,  # Yaz düşüşü
        8: 0.80,  # Yaz düşüşü
        9: 1.15,  # Yoğun
        10: 1.05, # Normal
        11: 1.00, # Normal
        12: 0.95  # Normal
    },
    'Antalya': {
        4: 1.15,  # Turizm
        5: 1.20,  # Turizm
        6: 1.25,  # Yaz başlangıcı
        7: 1.30,  # Yaz
        8: 1.30,  # Yaz
        9: 1.20,  # Turizm devam
        10: 1.10, # Turizm azalıyor
        11: 1.05, # Normal
        12: 1.15  # Kış turizmi
    }
}

# Bölgesel ve mevsimsel tahminler
print("\nBölgesel ve Mevsimsel Tahminler:")
for bolge in df['Bolge'].unique():
    bolge_data = df[df['Bolge'] == bolge]
    avg_daily = bolge_data['Gunluk_Ortalama'].mean()
    
    print(f"\n{bolge} Bölgesi:")
    for month in range(4, 13):
        base_pred = int(avg_daily * working_days[month])
        seasonal_factor = seasonal_regional_factors[bolge][month]
        seasonal_pred = int(base_pred * seasonal_factor)
        
        print(f"2024-{month:02d}: {seasonal_pred} ticket")
        print(f"         Baz tahmin: {base_pred}")
        print(f"         Mevsimsel faktör: {seasonal_factor:.2f}")

# Grafik ayarları
plt.style.use('default')
plt.rcParams['figure.figsize'] = [20, 12]
plt.rcParams['font.size'] = 10
plt.rcParams['lines.linewidth'] = 2
plt.rcParams['lines.markersize'] = 8

# Her bölge için ayrı grafik
fig = plt.figure()

# Bölgeleri döngüye al
for idx, bolge in enumerate(df['Bolge'].unique(), 1):
    ax = plt.subplot(2, 3, idx)
    
    # Veri hazırla
    months = list(range(1, 13))
    tickets = []
    
    # İlk 3 ay gerçek veriler
    bolge_data = df[df['Bolge'] == bolge]
    real_tickets = bolge_data['Ticket_Sayisi'].tolist()
    
    # Kalan aylar tahmin
    avg_daily = bolge_data['Gunluk_Ortalama'].mean()
    for month in range(4, 13):
        base_pred = int(avg_daily * working_days[month])
        seasonal_pred = int(base_pred * seasonal_regional_factors[bolge][month])
        tickets.append(seasonal_pred)
    
    # Tüm verileri birleştir
    all_tickets = real_tickets + tickets
    
    # Grafiği çiz
    ax.plot(months, all_tickets, 'o-', color='blue')
    
    # Gerçek ve tahmin verilerini ayır
    ax.axvline(x=3.5, color='red', linestyle='--', alpha=0.3, label='Tahmin Başlangıcı')
    
    # Grafik özellikleri
    ax.set_title(f'{bolge} Bölgesi Ticket Tahminleri')
    ax.set_xlabel('Ay')
    ax.set_ylabel('Ticket Sayısı')
    ax.grid(True, alpha=0.3)
    
    # X ekseni ayarları
    ax.set_xticks(months)
    ax.set_xticklabels(['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 
                        'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'])

plt.tight_layout()
plt.savefig('bolgesel_tahminler.png')  # Grafiği dosyaya kaydet
plt.close()

# Karşılaştırmalı grafik için
plt.figure(figsize=(15, 8))
colors = ['blue', 'red', 'green', 'purple', 'orange', 'brown']

for idx, bolge in enumerate(df['Bolge'].unique()):
    bolge_data = df[df['Bolge'] == bolge]
    real_tickets = bolge_data['Ticket_Sayisi'].tolist()
    
    avg_daily = bolge_data['Gunluk_Ortalama'].mean()
    tickets = []
    for month in range(4, 13):
        base_pred = int(avg_daily * working_days[month])
        seasonal_pred = int(base_pred * seasonal_regional_factors[bolge][month])
        tickets.append(seasonal_pred)
    
    all_tickets = real_tickets + tickets
    plt.plot(months, all_tickets, 'o-', label=bolge, color=colors[idx])

plt.axvline(x=3.5, color='red', linestyle='--', alpha=0.3, label='Tahmin Başlangıcı')
plt.title('Bölgelere Göre Ticket Tahminleri')
plt.xlabel('Ay')
plt.ylabel('Ticket Sayısı')
plt.grid(True, alpha=0.3)
plt.legend()
plt.xticks(months, ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 
                    'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'])

# Dosya yolunu belirle
dosya_yolu = 'D:/PhytonEgitimleri/karsilastirmali_tahmin.png'

# Kaydetmeyi dene ve sonucu kontrol et
try:
    plt.savefig(dosya_yolu)
    print(f"Grafik kaydedildi: {dosya_yolu}")
    if os.path.exists(dosya_yolu):
        print(f"Dosya başarıyla oluşturuldu, boyutu: {os.path.getsize(dosya_yolu)} bytes")
    else:
        print("Dosya oluşturulamadı!")
except Exception as e:
    print(f"Hata oluştu: {e}")

plt.close()

print("Çalışma dizini:", os.getcwd())