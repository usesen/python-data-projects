import random
from datetime import datetime, timedelta
import pyodbc
import numpy as np

# Kategoriler ve alt kategoriler
kategoriler = {
    'Donanım': ['PC Arıza', 'Yazıcı Arıza', 'Ağ Donanımı'],
    'Yazılım': ['Office', 'ERP', 'İşletim Sistemi'],
    'Ağ': ['VPN', 'İnternet', 'Ağ Erişimi']
}

# Çözüm detayları
cozum_detaylari = {
    'Donanım': {
        'PC Arıza': {
            'Yavaşlık': [
                'RAM bellek temizliği yapıldı, soğutucu macun yenilendi',
                'Disk birleştirme yapıldı, gereksiz dosyalar temizlendi',
                'İşlemci soğutucu fanı temizlendi',
                'BIOS ayarları kontrol edildi ve güncellendi'
            ],
            'Fan Sesi': [
                'Fan temizliği yapıldı',
                'Fan yağlaması yapıldı',
                'Fan değişimi yapıldı',
                'Termal macun yenilendi'
            ]
        },
        'Yazıcı Arıza': {
            'Kağıt Sıkışması': [
                'Kağıt yolu temizlendi, bakım yapıldı',
                'Pickup roller değiştirildi',
                'Kağıt sensörleri temizlendi',
                'Yazıcı firmware güncellendi'
            ],
            'Baskı Kalitesi': [
                'Toner/kartuş değiştirildi',
                'Drum ünitesi değiştirildi',
                'Kalibrasyon yapıldı',
                'Yazıcı kafası temizlendi'
            ]
        }
    },
    'Yazılım': {
        'Office': {
            'Excel': [
                'Office önbelleği temizlendi',
                'Excel ayarları sıfırlandı',
                'Office onarıldı',
                'Office kaldırılıp yeniden kuruldu'
            ],
            'Outlook': [
                'Outlook profili yeniden oluşturuldu',
                'OST dosyası yeniden oluşturuldu',
                'Exchange bağlantısı yeniden yapılandırıldı',
                'Outlook güvenli modda başlatıldı ve onarıldı'
            ]
        },
        'ERP': {
            'SAP': [
                'SAP GUI önbelleği temizlendi',
                'SAP oturum parametreleri sıfırlandı',
                'SAP GUI yeniden kuruldu',
                'Sistem bağlantı testi yapıldı'
            ]
        }
    },
    'Ağ': {
        'VPN': {
            'Bağlantı': [
                'VPN client yeniden başlatıldı',
                'VPN ayarları kontrol edildi',
                'DNS ayarları güncellendi',
                'Firewall kuralları kontrol edildi'
            ],
            'Performans': [
                'Ağ kartı sürücüleri güncellendi',
                'MTU değeri optimize edildi',
                'Split tunneling ayarları yapıldı',
                'QoS ayarları kontrol edildi'
            ]
        }
    }
}

# Problem açıklamaları
problem_detaylari = {
    'PC Arıza': [
        'Bilgisayar çok yavaş açılıyor ve fan sesi çok yüksek',
        'Bilgisayar sürekli donuyor ve yeniden başlıyor',
        'Ekran görüntüsü gelmiyor, sadece ses var'
    ],
    'Yazıcı Arıza': [
        'Yazıcı kağıt sıkıştırıyor ve hata veriyor',
        'Çıktılar silik ve soluk çıkıyor',
        'Yazıcı ağda görünmüyor'
    ],
    'Office': [
        'Excel dosyası açılmıyor, sürekli kilitleniyor',
        'Outlook sürekli yanıt vermiyor hatası veriyor',
        'Word belgeleri kaydedilemiyor'
    ],
    'ERP': [
        'SAP sistemine giriş yapılamıyor',
        'SAP ekranı donuyor ve yanıt vermiyor',
        'SAP raporları açılmıyor'
    ],
    'VPN': [
        'VPN bağlantısı kurulamıyor, timeout hatası',
        'VPN bağlantısı çok yavaş',
        'VPN sürekli kopuyor'
    ]
}

def get_solution_detail(kategori, alt_kategori, problem_tipi):
    try:
        cozumler = cozum_detaylari[kategori][alt_kategori][problem_tipi]
        return random.choice(cozumler)
    except KeyError:
        return "Standart prosedür uygulandı"

def test_verisi_olustur():
    # SQL Server bağlantısı
    conn = pyodbc.connect('DRIVER={SQL Server};SERVER=DESKTOP-6QR83E3\\UGURMSSQL;DATABASE=FSM_Tickets;UID=usesen;PWD=usesen')
    cursor = conn.cursor()

    try:
        # Önce tabloyu kontrol et ve varsa sil
        cursor.execute("""
        IF OBJECT_ID('dbo.Tickets', 'U') IS NOT NULL 
            DROP TABLE dbo.Tickets
        """)
        conn.commit()
        print("Eski tablo silindi.")

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
            [Cozum_Aciklamasi] NVARCHAR(MAX),
            [Problem_Aciklamasi] NVARCHAR(MAX),
            [Yapilan_Islem] NVARCHAR(MAX),
            [Kullanilan_Arac] NVARCHAR(MAX),
            [Root_Cause] NVARCHAR(MAX),
            PRIMARY KEY ([Ticket_ID])
        )
        """)
        print("Yeni tablo oluşturuldu.")
        
        # Veri oluştur ve ekle
        baslangic_tarih = datetime(2023, 1, 1)
        bitis_tarih = datetime(2024, 1, 31)
        
        TOPLAM_KAYIT = 50000
        
        for i in range(1, TOPLAM_KAYIT + 1):
            ticket_id = f'TIC{i:06d}'
            
            # Kategori ve alt kategori seç
            kategori = random.choice(list(kategoriler.keys()))
            alt_kategori = random.choice(kategoriler[kategori])
            
            # Problem ve çözüm detaylarını seç
            if alt_kategori in problem_detaylari:
                problem = random.choice(problem_detaylari[alt_kategori])
                
                # Problem tipini belirle
                if 'yavaş' in problem.lower():
                    problem_tipi = 'Yavaşlık'
                elif 'bağlantı' in problem.lower() or 'vpn' in problem.lower():
                    problem_tipi = 'Bağlantı'
                elif 'kağıt' in problem.lower():
                    problem_tipi = 'Kağıt Sıkışması'
                elif 'excel' in problem.lower():
                    problem_tipi = 'Excel'
                elif 'outlook' in problem.lower():
                    problem_tipi = 'Outlook'
                elif 'sap' in problem.lower():
                    problem_tipi = 'SAP'
                else:
                    problem_tipi = 'Yavaşlık'  # Varsayılan tip
                
                cozum = get_solution_detail(kategori, alt_kategori, problem_tipi)
            else:
                problem = "Standart problem"
                cozum = "Standart prosedür uygulandı"

            # Diğer alanları oluştur
            bolge = random.choice(['İstanbul', 'Ankara', 'İzmir', 'Bursa', 'Antalya'])
            oncelik = random.choice(['Düşük', 'Orta', 'Yüksek', 'Kritik'])
            teknisyen = f'Teknisyen_{random.randint(1,10)}'
            teknisyen_seviye = random.choice(['Junior', 'Mid-Level', 'Senior'])
            
            # Tarihleri oluştur
            olusturma_tarihi = baslangic_tarih + timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            atama_tarihi = olusturma_tarihi + timedelta(minutes=random.randint(5, 120))
            cozum_tarihi = atama_tarihi + timedelta(minutes=random.randint(30, 480))
            
            # İş günü ve mesai kontrolü
            is_gununde = 1 if olusturma_tarihi.weekday() < 5 else 0
            mesai_saatinde = 1 if 9 <= olusturma_tarihi.hour <= 18 else 0
            
            # SLA süreleri
            hedef_atama = 60 if oncelik == 'Kritik' else 120
            hedef_cozum = 240 if oncelik == 'Kritik' else 480
            
            gercek_atama = int((atama_tarihi - olusturma_tarihi).total_seconds() / 60)
            gercek_cozum = int((cozum_tarihi - atama_tarihi).total_seconds() / 60)
            
            # SLA uyumları
            atama_sla = 1 if gercek_atama <= hedef_atama else 0
            cozum_sla = 1 if gercek_cozum <= hedef_cozum else 0
            
            # Müşteri memnuniyeti
            memnuniyet = round(random.uniform(3.0, 5.0), 1)
            
            # Yapılan işlem ve kullanılan araçlar
            yapilan_islem = f"1-Problem analizi yapıldı\n2-{cozum}"
            kullanilan_arac = random.choice(['Remote Desktop', 'TeamViewer', 'VNC', 'Yerinde Müdahale'])
            
            # Root cause
            root_cause = random.choice([
                'Kullanıcı Hatası',
                'Donanım Arızası',
                'Yazılım Hatası',
                'Ağ Problemi',
                'Sistem Güncellemesi'
            ])

            # Verileri ekle
            cursor.execute("""
            INSERT INTO Tickets (
                Ticket_ID, Bolge, Oncelik, Kategori, Alt_Kategori,
                Teknisyen, Teknisyen_Seviye, Olusturma_Tarihi,
                Atama_Tarihi, Cozum_Tarihi, Is_Gununde_mi,
                Mesai_Saatinde_mi, Hedef_Atama_Suresi_dk,
                Gercek_Atama_Suresi_dk, Hedef_Cozum_Suresi_dk,
                Gercek_Cozum_Suresi_dk, Atama_SLA_Uyumu,
                Cozum_SLA_Uyumu, Musteri_Memnuniyeti,
                Problem_Aciklamasi, Cozum_Aciklamasi,
                Yapilan_Islem, Kullanilan_Arac, Root_Cause
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticket_id, bolge, oncelik, kategori, alt_kategori,
                teknisyen, teknisyen_seviye, olusturma_tarihi,
                atama_tarihi, cozum_tarihi, is_gununde,
                mesai_saatinde, hedef_atama, gercek_atama,
                hedef_cozum, gercek_cozum, atama_sla, cozum_sla,
                memnuniyet, problem, cozum, yapilan_islem,
                kullanilan_arac, root_cause
            ))

            if i % 1000 == 0:
                print(f"{i} adet ticket oluşturuldu ({(i/TOPLAM_KAYIT)*100:.1f}%)")
                conn.commit()

        conn.commit()
        print(f"Toplam {TOPLAM_KAYIT} adet ticket başarıyla oluşturuldu.")

    except Exception as e:
        print("Hata:", str(e))
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    test_verisi_olustur()