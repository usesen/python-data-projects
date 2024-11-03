# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Rastgele veri üretimi için seed belirleme
np.random.seed(42)

# Örnek veri oluşturma
n_kayit = 200  # 200 servis kaydı

# Tarih aralığı oluşturma (son 30 gün)
tarihler = pd.date_range(end='2024-03-20', periods=n_kayit, freq='H')

veri = {
    'cagri_id': range(1, n_kayit + 1),
    'tarih': tarihler,
    'teknisyen': np.random.choice(['Ahmet', 'Mehmet', 'Ayşe', 'Fatma', 'Ali'], n_kayit),
    'oncelik': np.random.choice(['Düşük', 'Orta', 'Yüksek', 'Kritik'], n_kayit, p=[0.3, 0.4, 0.2, 0.1]),
    'kategori': np.random.choice(['Donanım', 'Yazılım', 'Ağ', 'Elektrik', 'Bakım'], n_kayit),
    'cozum_suresi_dk': np.random.normal(120, 30, n_kayit).round(),  # Ortalama 2 saat
    'musteri_memnuniyeti': np.random.randint(1, 6, n_kayit),  # 1-5 arası puanlama
    'maliyet_tl': np.random.normal(500, 150, n_kayit).round(),
}

# DataFrame oluşturma
df = pd.DataFrame(veri)

# Temel analizler
print("\n=== Servis Çağrıları Analizi ===")
print("\nTeknisyen Bazlı Performans:")
teknisyen_analiz = df.groupby('teknisyen').agg({
    'cagri_id': 'count',
    'cozum_suresi_dk': 'mean',
    'musteri_memnuniyeti': 'mean',
    'maliyet_tl': 'mean'
}).round(2)
print(teknisyen_analiz)

# Görselleştirmeler
plt.figure(figsize=(15, 10))

# 1. Teknisyen başına ortalama çözüm süresi
plt.subplot(2, 2, 1)
sns.barplot(data=df, x='teknisyen', y='cozum_suresi_dk')
plt.title('Teknisyen Başına Ortalama Çözüm Süresi')
plt.xticks(rotation=45)
plt.ylabel('Dakika')

# 2. Kategori bazlı çağrı dağılımı
plt.subplot(2, 2, 2)
df['kategori'].value_counts().plot(kind='pie', autopct='%1.1f%%')
plt.title('Kategori Bazlı Çağrı Dağılımı')

# 3. Öncelik seviyelerine göre çözüm süreleri
plt.subplot(2, 2, 3)
sns.boxplot(data=df, x='oncelik', y='cozum_suresi_dk')
plt.title('Öncelik Seviyelerine Göre Çözüm Süreleri')
plt.xticks(rotation=45)
plt.ylabel('Dakika')

# 4. Müşteri memnuniyeti dağılımı
plt.subplot(2, 2, 4)
sns.histplot(data=df, x='musteri_memnuniyeti', bins=5)
plt.title('Müşteri Memnuniyeti Dağılımı')
plt.xlabel('Memnuniyet Puanı (1-5)')

plt.tight_layout()
plt.show()

# İstatistiksel analizler
print("\n=== Detaylı İstatistikler ===")
print("\nKategori Bazlı Ortalama Çözüm Süreleri:")
print(df.groupby('kategori')['cozum_suresi_dk'].mean().round(2))

print("\nÖncelik Bazlı Ortalama Maliyet:")
print(df.groupby('oncelik')['maliyet_tl'].mean().round(2))

# Verimlilik analizi
df['gun'] = df['tarih'].dt.date
gunluk_analiz = df.groupby('gun').agg({
    'cagri_id': 'count',
    'cozum_suresi_dk': 'mean',
    'maliyet_tl': 'sum'
}).round(2)

print("\nGünlük Ortalama Performans:")
print(gunluk_analiz.mean().round(2))
