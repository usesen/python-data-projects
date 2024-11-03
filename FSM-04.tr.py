import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

# Seed for reproducibility
np.random.seed(42)

# Sabit veriler
BOLGELER = ['İstanbul-Avrupa', 'İstanbul-Anadolu', 'Ankara', 'İzmir', 'Antalya']
ONCELIKLER = ['Kritik', 'Yüksek', 'Orta', 'Düşük']
KATEGORILER = ['Donanım', 'Yazılım', 'Ağ', 'Elektrik', 'Bakım']
TEKNISYENLER = {
    'İstanbul-Avrupa': ['Ahmet Y.', 'Mehmet K.', 'Ali S.', 'Ayşe D.'],
    'İstanbul-Anadolu': ['Fatma B.', 'Mustafa Ö.', 'Zeynep A.'],
    'Ankara': ['Emre T.', 'Selin K.', 'Burak M.'],
    'İzmir': ['Deniz Ş.', 'Canan Y.'],
    'Antalya': ['Murat A.', 'Elif K.']
}

# SLA hedefleri (dakika cinsinden)
SLA_HEDEFLERI = {
    'Kritik': {'atama': 15, 'cozum': 120},
    'Yüksek': {'atama': 30, 'cozum': 240},
    'Orta': {'atama': 60, 'cozum': 480},
    'Düşük': {'atama': 120, 'cozum': 960}
}

def ticket_olustur(n_tickets):
    baslangic_tarihi = datetime(2024, 1, 1)
    
    tickets = []
    for i in range(n_tickets):
        ticket_id = f'TKT-{str(i+1).zfill(5)}'
        bolge = np.random.choice(BOLGELER, p=[0.3, 0.25, 0.2, 0.15, 0.1])
        oncelik = np.random.choice(ONCELIKLER, p=[0.1, 0.2, 0.4, 0.3])
        kategori = np.random.choice(KATEGORILER)
        
        olusturma_tarihi = baslangic_tarihi + timedelta(
            minutes=np.random.randint(0, 43200)
        )
        
        hedef_atama_suresi = SLA_HEDEFLERI[oncelik]['atama']
        gercek_atama_suresi = int(np.random.normal(
            hedef_atama_suresi, hedef_atama_suresi/4
        ))
        atama_tarihi = olusturma_tarihi + timedelta(minutes=gercek_atama_suresi)
        
        hedef_cozum_suresi = SLA_HEDEFLERI[oncelik]['cozum']
        gercek_cozum_suresi = int(np.random.normal(
            hedef_cozum_suresi, hedef_cozum_suresi/4
        ))
        cozum_tarihi = atama_tarihi + timedelta(minutes=gercek_cozum_suresi)
        
        teknisyen = np.random.choice(TEKNISYENLER[bolge])
        
        atama_sla = gercek_atama_suresi <= hedef_atama_suresi
        cozum_sla = gercek_cozum_suresi <= hedef_cozum_suresi
        
        if atama_sla and cozum_sla:
            memnuniyet = np.random.randint(4, 6)
        elif atama_sla or cozum_sla:
            memnuniyet = np.random.randint(3, 5)
        else:
            memnuniyet = np.random.randint(1, 4)
            
        tickets.append({
            'Ticket_ID': ticket_id,
            'Bölge': bolge,
            'Öncelik': oncelik,
            'Kategori': kategori,
            'Teknisyen': teknisyen,
            'Oluşturma_Tarihi': olusturma_tarihi,
            'Atama_Tarihi': atama_tarihi,
            'Çözüm_Tarihi': cozum_tarihi,
            'Hedef_Atama_Süresi_dk': hedef_atama_suresi,
            'Gerçek_Atama_Süresi_dk': gercek_atama_suresi,
            'Hedef_Çözüm_Süresi_dk': hedef_cozum_suresi,
            'Gerçek_Çözüm_Süresi_dk': gercek_cozum_suresi,
            'Atama_SLA_Uyumu': atama_sla,
            'Çözüm_SLA_Uyumu': cozum_sla,
            'Müşteri_Memnuniyeti': memnuniyet
        })
    
    return pd.DataFrame(tickets)

# Veriyi oluştur
df = ticket_olustur(500)

# Bundan sonraki kodlar aynı...

# Zaman bazlı analizler için yeni grafikler
plt.figure(figsize=(20, 12))

# 1. Günlük Ticket Dağılımı
plt.subplot(2, 3, 1)
df['Gün'] = df['Oluşturma_Tarihi'].dt.day
gunluk_dagilim = df['Gün'].value_counts().sort_index()
sns.barplot(data=pd.DataFrame({'Gün': gunluk_dagilim.index, 'Sayı': gunluk_dagilim.values}),
           x='Gün', y='Sayı', color='#3498db')
plt.title('Günlük Ticket Dağılımı', pad=20, fontsize=12)
plt.xlabel('Ayın Günü')
plt.ylabel('Ticket Sayısı')

# 2. Saatlik Yoğunluk
plt.subplot(2, 3, 2)
df['Saat'] = df['Oluşturma_Tarihi'].dt.hour
saatlik_yogunluk = df['Saat'].value_counts().sort_index()
sns.barplot(data=pd.DataFrame({'Saat': saatlik_yogunluk.index, 'Sayı': saatlik_yogunluk.values}),
           x='Saat', y='Sayı', color='#2ecc71')
plt.title('Saatlik Ticket Yoğunluğu', pad=20, fontsize=12)
plt.xlabel('Saat')
plt.ylabel('Ticket Sayısı')

# 3. Öncelik-Zaman Heatmap
plt.subplot(2, 3, 3)
oncelik_saat = pd.crosstab(df['Saat'], df['Öncelik'])
sns.heatmap(oncelik_saat, cmap='YlOrRd', annot=True, fmt='d')
plt.title('Saatlik Öncelik Dağılımı', pad=20, fontsize=12)

# 4. Ortalama Çözüm Süreleri Trendi
plt.subplot(2, 3, 4)
df['Gün_Saat'] = df['Oluşturma_Tarihi'].dt.strftime('%d-%H')
cozum_trend = df.groupby('Gün_Saat')['Gerçek_Çözüm_Süresi_dk'].mean()
plt.plot(range(len(cozum_trend)), cozum_trend.values, color='#e74c3c', linewidth=2)
plt.title('Ortalama Çözüm Süresi Trendi', pad=20, fontsize=12)
plt.xlabel('Zaman (Gün-Saat)')
plt.ylabel('Ortalama Çözüm Süresi (dk)')
plt.xticks(rotation=45)

# 5. Bölge-Saat Heatmap
plt.subplot(2, 3, 5)
bolge_saat = pd.crosstab(df['Saat'], df['Bölge'])
sns.heatmap(bolge_saat, cmap='viridis', annot=True, fmt='d')
plt.title('Bölgesel Saat Dağılımı', pad=20, fontsize=12)

# 6. SLA Uyum Trendi
plt.subplot(2, 3, 6)
sla_trend = df.groupby('Gün')['Çözüm_SLA_Uyumu'].mean() * 100
plt.plot(sla_trend.index, sla_trend.values, color='#9b59b6', marker='o', linewidth=2)
plt.title('Günlük SLA Uyum Trendi', pad=20, fontsize=12)
plt.xlabel('Ayın Günü')
plt.ylabel('SLA Uyum Oranı (%)')

plt.tight_layout(pad=3.0)
plt.show()

# Detaylı raporları yazdır
print("\n=== DETAYLI PERFORMANS RAPORU ===")

print("\n1. Günlük Ticket Dağılımı:")
print(gunluk_dagilim)

print("\n2. Saatlik Yoğunluk:")
print(saatlik_yogunluk)

print("\n3. Bölgesel SLA Performansı:")
bolge_sla = df.groupby('Bölge')['Çözüm_SLA_Uyumu'].agg(['mean', 'count']).round(3)
bolge_sla['mean'] = bolge_sla['mean'] * 100
print(bolge_sla)

print("\n4. Öncelik Bazlı Çözüm Süreleri:")
oncelik_analiz = df.groupby('Öncelik').agg({
    'Gerçek_Çözüm_Süresi_dk': ['mean', 'min', 'max'],
    'Çözüm_SLA_Uyumu': 'mean'
}).round(2)
print(oncelik_analiz)

# Excel'e kaydet
with pd.ExcelWriter('fsm_detayli_rapor.xlsx') as writer:
    df.to_excel(writer, sheet_name='Ham_Veri', index=False)
    gunluk_dagilim.to_excel(writer, sheet_name='Günlük_Dağılım')
    saatlik_yogunluk.to_excel(writer, sheet_name='Saatlik_Yoğunluk')
    bolge_sla.to_excel(writer, sheet_name='Bölge_SLA')
    oncelik_analiz.to_excel(writer, sheet_name='Öncelik_Analiz')

print("\nDetaylı rapor 'fsm_detayli_rapor.xlsx' dosyasına kaydedildi.")
