# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

# Türkçe karakter desteği
plt.rcParams['font.family'] = 'Arial'

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
        # Temel ticket bilgileri
        ticket_id = f'TKT-{str(i+1).zfill(5)}'
        bolge = np.random.choice(BOLGELER, p=[0.3, 0.25, 0.2, 0.15, 0.1])
        oncelik = np.random.choice(ONCELIKLER, p=[0.1, 0.2, 0.4, 0.3])
        kategori = np.random.choice(KATEGORILER)
        
        # Tarih ve süre hesaplamaları
        olusturma_tarihi = baslangic_tarihi + timedelta(
            minutes=np.random.randint(0, 43200)  # 30 gün içinde
        )
        
        # Atama süresi hesaplama
        hedef_atama_suresi = SLA_HEDEFLERI[oncelik]['atama']
        gercek_atama_suresi = int(np.random.normal(
            hedef_atama_suresi, hedef_atama_suresi/4
        ))
        atama_tarihi = olusturma_tarihi + timedelta(minutes=gercek_atama_suresi)
        
        # Çözüm süresi hesaplama
        hedef_cozum_suresi = SLA_HEDEFLERI[oncelik]['cozum']
        gercek_cozum_suresi = int(np.random.normal(
            hedef_cozum_suresi, hedef_cozum_suresi/4
        ))
        cozum_tarihi = atama_tarihi + timedelta(minutes=gercek_cozum_suresi)
        
        # Teknisyen atama
        teknisyen = np.random.choice(TEKNISYENLER[bolge])
        
        # SLA durumu hesaplama
        atama_sla = gercek_atama_suresi <= hedef_atama_suresi
        cozum_sla = gercek_cozum_suresi <= hedef_cozum_suresi
        
        # Memnuniyet skoru (SLA durumuna göre ağırlıklı)
        if atama_sla and cozum_sla:
            memnuniyet = np.random.randint(4, 6)  # 4-5
        elif atama_sla or cozum_sla:
            memnuniyet = np.random.randint(3, 5)  # 3-4
        else:
            memnuniyet = np.random.randint(1, 4)  # 1-3
            
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

# 500 ticket oluştur
df = ticket_olustur(500)

# Analiz ve Görselleştirmeler
plt.figure(figsize=(20, 12))

# 1. Bölge Bazlı Ticket Dağılımı
plt.subplot(2, 3, 1)
bolge_dagilim = df['Bölge'].value_counts()
ax1 = sns.barplot(x=bolge_dagilim.index, y=bolge_dagilim.values, palette='Blues_r')
plt.title('Bölge Bazlı Ticket Dağılımı', pad=20, fontsize=12)
plt.xticks(rotation=45)
plt.ylabel('Ticket Sayısı')

for i, v in enumerate(bolge_dagilim.values):
    ax1.text(i, v, str(v), ha='center', va='bottom')

# 2. SLA Uyum Oranları
plt.subplot(2, 3, 2)
sla_values = [df['Atama_SLA_Uyumu'].mean() * 100, df['Çözüm_SLA_Uyumu'].mean() * 100]
ax2 = plt.bar(['Atama SLA', 'Çözüm SLA'], sla_values, color=['#2ecc71', '#3498db'])
plt.title('Genel SLA Uyum Oranları (%)', pad=20, fontsize=12)
plt.ylabel('Uyum Yüzdesi')

for i, v in enumerate(sla_values):
    plt.text(i, v, f'%{v:.1f}', ha='center', va='bottom')

# 3. Öncelik Bazlı Ortalama Çözüm Süreleri
plt.subplot(2, 3, 3)
oncelik_sure = df.groupby('Öncelik')['Gerçek_Çözüm_Süresi_dk'].mean()
ax3 = sns.barplot(x=oncelik_sure.index, y=oncelik_sure.values, palette='Reds_r')
plt.title('Öncelik Bazlı Ort. Çözüm Süreleri', pad=20, fontsize=12)
plt.ylabel('Dakika')
plt.xticks(rotation=45)

for i, v in enumerate(oncelik_sure.values):
    ax3.text(i, v, f'{int(v)}dk', ha='center', va='bottom')

# 4. Teknisyen Performansı
plt.subplot(2, 3, 4)
teknisyen_perf = df.groupby('Teknisyen')['Çözüm_SLA_Uyumu'].mean().sort_values(ascending=False)
ax4 = sns.barplot(x=teknisyen_perf.index, y=teknisyen_perf.values * 100, palette='Greens_r')
plt.title('Teknisyen SLA Performansı', pad=20, fontsize=12)
plt.xticks(rotation=45)
plt.ylabel('SLA Uyum Yüzdesi')

for i, v in enumerate(teknisyen_perf.values):
    ax4.text(i, v*100, f'%{v*100:.1f}', ha='center', va='bottom')

# 5. Kategori Bazlı Ticket Dağılımı
plt.subplot(2, 3, 5)
kategori_dagilim = df['Kategori'].value_counts()
plt.pie(kategori_dagilim.values, labels=kategori_dagilim.index, autopct='%1.1f%%')
plt.title('Kategori Bazlı Ticket Dağılımı', pad=20, fontsize=12)

# 6. Müşteri Memnuniyeti Dağılımı
plt.subplot(2, 3, 6)
memnuniyet_dagilim = df['Müşteri_Memnuniyeti'].value_counts().sort_index()
ax6 = sns.barplot(x=memnuniyet_dagilim.index, y=memnuniyet_dagilim.values, palette='Purples_r')
plt.title('Müşteri Memnuniyeti Dağılımı', pad=20, fontsize=12)
plt.xlabel('Memnuniyet Skoru')
plt.ylabel('Ticket Sayısı')

for i, v in enumerate(memnuniyet_dagilim.values):
    ax6.text(i, v, str(v), ha='center', va='bottom')

plt.tight_layout(pad=3.0)
plt.show()

# Özet istatistikler yazdırma
print("\n=== Özet İstatistikler ===")
print(f"\nToplam Ticket Sayısı: {len(df)}")
print(f"Genel SLA Uyum Oranı: %{df['Çözüm_SLA_Uyumu'].mean()*100:.1f}")
print(f"Ortalama Müşteri Memnuniyeti: {df['Müşteri_Memnuniyeti'].mean():.2f}/5")

# Excel'e kaydet
df.to_excel('fsm_tickets.xlsx', index=False)


