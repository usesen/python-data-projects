# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Örnek veri oluşturma
np.random.seed(42)  # Tekrar üretilebilir sonuçlar için
veri = {
    'yas': np.random.randint(20, 65, 100),
    'maas': np.random.randint(3000, 15000, 100),
    'deneyim_yili': np.random.randint(0, 30, 100),
    'departman': np.random.choice(['IT', 'Satış', 'Pazarlama', 'İK', 'Finans'], 100)
}

# DataFrame oluşturma
df = pd.DataFrame(veri)

# CSV dosyasına kaydetme
df.to_csv('veriler.csv', index=False)

# Veri okuma
df = pd.read_csv('veriler.csv')

# Temel veri analizi
print("\nİlk 5 satır:")
print(df.head())
print("\nİstatistiksel özet:")
print(df.describe())
print("\nVeri seti bilgisi:")
print(df.info())

# Yaş dağılımı
plt.figure(figsize=(10,6))
plt.hist(df['yas'], bins=20, edgecolor='black')
plt.title('Yaş Dağılımı')
plt.xlabel('Yaş')
plt.ylabel('Frekans')
plt.grid(True, alpha=0.3)
plt.show()

# Maaş kutu grafiği - departmanlara göre
plt.figure(figsize=(12,6))
sns.boxplot(x=df['departman'], y=df['maas'])
plt.title('Departmanlara Göre Maaş Dağılımı')
plt.xlabel('Departman')
plt.ylabel('Maaş (TL)')
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)
plt.show()

# Deneyim yılı ve maaş ilişkisi
plt.figure(figsize=(10,6))
plt.scatter(df['deneyim_yili'], df['maas'], alpha=0.5)
plt.title('Deneyim Yılı ve Maaş İlişkisi')
plt.xlabel('Deneyim Yılı')
plt.ylabel('Maaş (TL)')
plt.grid(True, alpha=0.3)
plt.show()
