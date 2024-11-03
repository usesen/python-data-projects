# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Rastgele veri üretimi için seed belirleme
np.random.seed(42)

# Bölgeler ve proje detayları
bolgeler = ['İstanbul-Avrupa', 'İstanbul-Anadolu', 'Ankara', 'İzmir', 'Antalya']
proje_tipleri = ['Kurulum', 'Bakım', 'Arıza', 'Güncelleme']
teknisyen_sayilari = {'İstanbul-Avrupa': 8, 'İstanbul-Anadolu': 6, 
                      'Ankara': 5, 'İzmir': 4, 'Antalya': 3}

# Veri oluşturma (500 iş emri)
n_kayit = 500
veri = {
    'is_emri_id': range(1, n_kayit + 1),
    'bolge': np.random.choice(bolgeler, n_kayit, p=[0.3, 0.25, 0.2, 0.15, 0.1]),
    'proje_tipi': np.random.choice(proje_tipleri, n_kayit),
    'tamamlanma_suresi_saat': np.random.normal(4, 1, n_kayit).round(1),
    'maliyet_tl': np.random.normal(1000, 200, n_kayit).round(2),
    'musteri_memnuniyeti': np.random.randint(1, 6, n_kayit),  # 1-5 arası
    'ekipman_sayisi': np.random.randint(1, 10, n_kayit)
}

# DataFrame oluşturma
df = pd.DataFrame(veri)

# Bölge bazlı performans hesaplamaları
df['verimlilik'] = df['ekipman_sayisi'] / df['tamamlanma_suresi_saat']
df['birim_maliyet'] = df['maliyet_tl'] / df['ekipman_sayisi']

# Bölgesel analiz
print("\n=== Bölgesel Performans Analizi ===")
bolge_analiz = df.groupby('bolge').agg({
    'is_emri_id': 'count',
    'tamamlanma_suresi_saat': 'mean',
    'maliyet_tl': 'mean',
    'musteri_memnuniyeti': 'mean',
    'verimlilik': 'mean'
}).round(2)

print("\nBölge Bazlı Analiz:")
print(bolge_analiz)

# Görselleştirmeler
plt.figure(figsize=(15, 10))

# 1. Bölge bazlı iş emri dağılımı
plt.subplot(2, 2, 1)
ax1 = sns.barplot(data=df, x='bolge', y='is_emri_id', 
                 estimator=lambda x: len(x), color='#2E86C1')
plt.title('Bölge Bazlı İş Emri Dağılımı', pad=20)
plt.ylabel('İş Emri Sayısı')
plt.xticks(rotation=45)

# Değerleri çubukların üzerine ekleme
for i in ax1.containers:
    ax1.bar_label(i, padding=3)

# 2. Bölge ve proje tipi bazlı maliyet analizi
plt.subplot(2, 2, 2)
ax2 = sns.boxplot(data=df, x='bolge', y='maliyet_tl', hue='proje_tipi')
plt.title('Bölge ve Proje Bazlı Maliyet Dağılımı', pad=20)
plt.ylabel('Maliyet (TL)')
plt.xticks(rotation=45)
plt.legend(title='Proje Tipi', bbox_to_anchor=(1.05, 1))

# 3. Bölge bazlı müşteri memnuniyeti
plt.subplot(2, 2, 3)
ax3 = sns.barplot(data=df, x='bolge', y='musteri_memnuniyeti', color='#2E86C1')
plt.title('Bölge Bazlı Müşteri Memnuniyeti', pad=20)
plt.ylabel('Ortalama Memnuniyet (1-5)')
plt.xticks(rotation=45)

# Değerleri çubukların üzerine ekleme
for i in ax3.containers:
    ax3.bar_label(i, fmt='%.1f', padding=3)

# 4. Bölge bazlı verimlilik
plt.subplot(2, 2, 4)
ax4 = sns.barplot(data=df, x='bolge', y='verimlilik', color='#2E86C1')
plt.title('Bölge Bazlı Verimlilik', pad=20)
plt.ylabel('Verimlilik (Ekipman/Saat)')
plt.xticks(rotation=45)

# Değerleri çubukların üzerine ekleme
for i in ax4.containers:
    ax4.bar_label(i, fmt='%.2f', padding=3)

plt.tight_layout(pad=3.0)
plt.show()

# Detaylı proje analizi
print("\n=== Proje Tipi Bazlı Analiz ===")
proje_analiz = df.groupby(['bolge', 'proje_tipi']).agg({
    'is_emri_id': 'count',
    'maliyet_tl': ['mean', 'sum'],
    'musteri_memnuniyeti': 'mean'
}).round(2)

print("\nProje ve Bölge Bazlı Detaylı Analiz:")
print(proje_analiz)

# Verimlilik analizi
print("\n=== Verimlilik Analizi ===")
verimlilik_analiz = df.groupby('bolge').agg({
    'verimlilik': ['mean', 'min', 'max'],
    'birim_maliyet': 'mean'
}).round(2)

print("\nBölge Bazlı Verimlilik Metrikleri:")
print(verimlilik_analiz)
