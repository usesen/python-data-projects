import pyodbc
import random
from datetime import datetime, timedelta
import numpy as np

def test_verisi_olustur():
    # SQL Server Bağlantısı
    conn = pyodbc.connect('DRIVER={SQL Server};SERVER=DESKTOP-6QR83E3\\UGURMSSQL;DATABASE=FSM_Tickets;UID=usesen;PWD=usesen')
    cursor = conn.cursor()

    # Tickets tablosunu sil
    cursor.execute("DROP TABLE IF EXISTS Tickets")
    conn.commit()

    # Tabloyu oluştur
    cursor.execute("""
    CREATE TABLE [dbo].[Tickets] (
        [Ticket_ID] VARCHAR(10),
        [Bolge] NVARCHAR(50),
        [Oncelik] NVARCHAR(20),
        [Kategori] NVARCHAR(20),
        [Alt_Kategori] NVARCHAR(50),
        [Teknisyen] NVARCHAR(50),
        [Teknisyen_Seviye] NVARCHAR(20),
        [Olusturma_Tarihi] DATETIME,
        [Atama_Tarihi] DATETIME,
        [Cozum_Tarihi] DATETIME,
        [Is_Gununde_mi] BIT,
        [Mesai_Saatinde_mi] BIT,
        [Hedef_Atama_Suresi_dk] INT,
        [Gercek_Atama_Suresi_dk] INT,
        [Hedef_Cozum_Suresi_dk] INT,
        [Gercek_Cozum_Suresi_dk] INT,
        [Atama_SLA_Uyumu] BIT,
        [Cozum_SLA_Uyumu] BIT,
        [Musteri_Memnuniyeti] FLOAT,
        [Cozum_Detay] NVARCHAR(50),
        [Tekrar_Acilma] BIT,
        [Onceki_Ticket_ID] VARCHAR(10) NULL,
        [Kaynak_Sistem] NVARCHAR(50),
        PRIMARY KEY ([Ticket_ID])
    )
    """)
    conn.commit()

    # Sabit listeler
    # Bölgelere göre ağırlıklar (büyük şehirlerde daha fazla ticket)
    bolge_agirliklari = {
        'İstanbul-Avrupa': 0.25,    # %25
        'İstanbul-Anadolu': 0.20,   # %20
        'Ankara': 0.20,             # %20
        'İzmir': 0.15,              # %15
        'Bursa': 0.10,              # %10
        'Antalya': 0.10             # %10
    }
    
    oncelikler = ['Yüksek', 'Orta', 'Düşük']
    teknisyenler = {
        'İstanbul-Avrupa': {
            'Ahmet Yılmaz': 'Senior',
            'Berk Demir': 'Senior',
            'Ayşe Kaya': 'Mid-Level',
            'Can Yıldız': 'Junior',
            'Zeynep Aksoy': 'Junior'
        },
        'İstanbul-Anadolu': {
            'Ali Öztürk': 'Senior',
            'Fatma Şahin': 'Senior',
            'Murat Aydın': 'Mid-Level',
            'Hakan Yılmaz': 'Junior'
        },
        'Ankara': {
            'Kemal Demir': 'Senior',
            'Selin Kaya': 'Senior',
            'Burak Öz': 'Mid-Level',
            'Deniz Yıldırım': 'Junior'
        },
        'İzmir': {
            'Canan Aksoy': 'Senior',
            'Serkan Yılmaz': 'Mid-Level',
            'Elif Demir': 'Junior',
            'Onur Kaya': 'Junior'
        },
        'Bursa': {
            'Levent Aydın': 'Senior',
            'Gül Şahin': 'Mid-Level',
            'Emre Yıldız': 'Junior'
        },
        'Antalya': {
            'Özlem Demir': 'Senior',
            'Tolga Kaya': 'Mid-Level',
            'Pınar Yılmaz': 'Junior'
        }
    }
    kategoriler = {
        'Donanım': ['PC Arıza', 'Yazıcı Arıza', 'Network Cihaz'],
        'Yazılım': ['Windows', 'Office', 'ERP', 'CRM'],
        'Ağ': ['İnternet', 'VPN', 'Firewall'],
        'Güvenlik': ['Virüs', 'Şifre Reset', 'Yetkilendirme'],
        'Veritabanı': ['SQL Server', 'Oracle', 'PostgreSQL']
    }
    cozum_detaylar = ['Yerinde', 'Uzaktan', 'Telefonla']
    kaynak_sistemler = ['Portal', 'Email', 'Telefon']

    # Tarih aralığı (3 ay)
    baslangic_tarih = datetime(2024, 1, 1)
    bitis_tarih = datetime(2024, 3, 31)

    # Her gün için veri oluştur
    current_date = baslangic_tarih
    ticket_counter = 1

    while current_date <= bitis_tarih:
        # Her gün için ticket sayısını belirle
        if current_date.weekday() < 5:  # Hafta içi
            gun_ticket_sayisi = random.randint(200, 300)
        else:  # Hafta sonu
            gun_ticket_sayisi = random.randint(50, 100)

        for _ in range(gun_ticket_sayisi):
            ticket_id = f'TIC{str(ticket_counter).zfill(6)}'
            
            # Bölge seçimi - ağırlıklı
            bolge = random.choices(
                list(bolge_agirliklari.keys()), 
                weights=list(bolge_agirliklari.values())
            )[0]

            # Saat belirle
            if random.random() < 0.8:  # %80 mesai saati
                saat = random.randint(9, 17)
                mesai_saatinde = 1
            else:
                saat = random.randint(0, 23)
                mesai_saatinde = 0

            # Tarihler
            olusturma_tarihi = current_date.replace(hour=saat, minute=random.randint(0, 59))
            
            # Öncelik ve hedef süreler
            oncelik = random.choice(oncelikler)
            hedef_atama = {'Yüksek': 60, 'Orta': 120, 'Düşük': 240}[oncelik]
            hedef_cozum = {'Yüksek': 240, 'Orta': 480, 'Düşük': 1440}[oncelik]

            # Gerçek süreler
            atama_suresi = random.randint(15, 480)
            cozum_suresi = random.randint(60, 2880)
            
            atama_tarihi = olusturma_tarihi + timedelta(minutes=atama_suresi)
            cozum_tarihi = atama_tarihi + timedelta(minutes=cozum_suresi)

            # Kategori seçimi
            kategori = random.choice(list(kategoriler.keys()))
            alt_kategori = random.choice(kategoriler[kategori])

            # Seçilen bölgenin teknisyenleri arasından seçim yap
            bolge_teknisyenleri = teknisyenler[bolge]  # Sadece o bölgenin teknisyenlerini al
            teknisyen = random.choice(list(bolge_teknisyenleri.keys()))
            teknisyen_seviye = bolge_teknisyenleri[teknisyen]

            # SLA uyumları
            atama_sla = 1 if atama_suresi <= hedef_atama else 0
            cozum_sla = 1 if cozum_suresi <= hedef_cozum else 0

            # Müşteri memnuniyeti
            musteri_memnuniyeti = random.uniform(0.7, 1.0) if (atama_sla and cozum_sla) else random.uniform(0.3, 0.8)

            # Tekrar açılma
            tekrar_acilma = random.choice([0, 0, 0, 1])  # %25 ihtimal
            onceki_ticket = f'TIC{str(random.randint(1, ticket_counter-1)).zfill(6)}' if tekrar_acilma and ticket_counter > 1 else None

            cursor.execute("""
            INSERT INTO Tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticket_id, bolge, oncelik, kategori, alt_kategori,
                teknisyen, teknisyen_seviye, olusturma_tarihi, atama_tarihi, cozum_tarihi,
                1 if olusturma_tarihi.weekday() < 5 else 0, mesai_saatinde,
                hedef_atama, atama_suresi, hedef_cozum, cozum_suresi,
                atama_sla, cozum_sla, musteri_memnuniyeti,
                random.choice(cozum_detaylar), tekrar_acilma, onceki_ticket,
                random.choice(kaynak_sistemler)
            ))

            ticket_counter += 1

        current_date += timedelta(days=1)

    conn.commit()
    conn.close()
    print(f"Test verisi başarıyla oluşturuldu! Toplam {ticket_counter-1} kayıt eklendi.")

if __name__ == "__main__":
    test_verisi_olustur()