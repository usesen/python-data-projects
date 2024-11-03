# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Rastgele veri üretimi için seed belirleme
np.random.seed(42)

# SLA süreleri (dakika cinsinden)
sla_hedefleri = {
    'Kritik': 60,    # 1 saat
    'Yüksek': 120,   # 2 saat
    'Orta': 240,     # 4 saat
    'Düşük': 480     # 8 saat
}

# Veri oluşturma (300 kayıt)
veri = {
    'ticket_id': range(1, 301),
    'oncelik': np.random.choice(['Düşük', 'Orta', 'Yüksek', 'Kritik'], 300),
    'teknisyen': np.random.choice(['Ahmet', 'Mehmet', 'Ayşe', 'Fatma'], 300),
    'kategori': np.random.choice(['Donanım', 'Yazılım', 'Ağ', 'Elektrik'], 300),
    'cozum_suresi_dk': np.random.normal(180, 60, 300).round()  # Ortalama 3 saat
}

# DataFrame oluşturma
df = pd.DataFrame(veri)

# SLA hesaplamaları
df['sla_hedef_dk'] = df['oncelik'].map(sla_hedefleri)
df['sla_gecikme_dk'] = df['cozum_suresi_dk'] - df['sla_hedef_dk']
df['sla_uyumu'] = (df['sla_gecikme_dk'] <= 0).astype(int)

# Temel analizler
print("\n=== SLA Performans Analizi ===")
print(f"\nGenel SLA Uyum Oranı: %{(df['sla_uyumu'].mean() * 100).round(1)}")

# Öncelik bazlı analiz
oncelik_analiz = df.groupby('oncelik').agg({
    'ticket_id': 'count',
    'sla_uyumu': 'mean',
    'cozum_suresi_dk': 'mean'
}).round(2)
oncelik_analiz['sla_uyumu'] = (oncelik_analiz['sla_uyumu'] * 100).round(1)
print("\nÖncelik Bazlı Analiz:")
print(oncelik_analiz)

# Grafik rengi
grafik_rengi = '#2E86C1'  # Mavi ton

plt.figure(figsize=(15, 10))

# 1. Öncelik bazlı SLA uyum oranları
plt.subplot(2, 2, 1)
ax1 = sns.barplot(data=df, x='oncelik', y='sla_uyumu', color=grafik_rengi)
plt.title('Öncelik Bazlı SLA Uyum', pad=20)
plt.ylabel('Uyum Oranı')
plt.xticks(rotation=45)

# Değerleri çubukların üzerine ekleme
for i in ax1.containers:
    ax1.bar_label(i, fmt='%.1f%%', padding=3)

# 2. Teknisyen bazlı ortalama çözüm süreleri
plt.subplot(2, 2, 2)
ax2 = sns.barplot(data=df, x='teknisyen', y='cozum_suresi_dk', color=grafik_rengi)
plt.title('Teknisyen Bazlı Çözüm Süreleri', pad=20)
plt.ylabel('Ortalama Çözüm Süresi (Dakika)')
plt.xticks(rotation=45)

# Değerleri çubukların üzerine ekleme
for i in ax2.containers:
    ax2.bar_label(i, fmt='%.0f dk', padding=3)

# 3. Kategori bazlı SLA uyum oranları
plt.subplot(2, 2, 3)
ax3 = sns.barplot(data=df, x='kategori', y='sla_uyumu', color=grafik_rengi)
plt.title('Kategori Bazlı SLA Uyum', pad=20)
plt.ylabel('Uyum Oranı')
plt.xticks(rotation=45)

# Değerleri çubukların üzerine ekleme
for i in ax3.containers:
    ax3.bar_label(i, fmt='%.1f%%', padding=3)

# 4. Çözüm süresi dağılımı
plt.subplot(2, 2, 4)
ax4 = plt.hist(df['cozum_suresi_dk'], bins=30, color=grafik_rengi, edgecolor='black')
plt.title('Çözüm Süresi Dağılımı', pad=20)
plt.xlabel('Dakika')
plt.ylabel('Çağrı Sayısı')

# Grafik düzeni ayarları
plt.tight_layout(pad=3.0)
plt.show()

# Teknisyen performans analizi
print("\nTeknisyen Performansı:")
teknisyen_analiz = df.groupby('teknisyen').agg({
    'ticket_id': 'count',
    'sla_uyumu': 'mean',
    'cozum_suresi_dk': 'mean'
}).round(2)
teknisyen_analiz['sla_uyumu'] = (teknisyen_analiz['sla_uyumu'] * 100).round(1)
print(teknisyen_analiz)
