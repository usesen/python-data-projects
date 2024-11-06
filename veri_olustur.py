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
            ],
            'Ekran': [
                'Ekran kartı sürücüleri güncellendi',
                'Ekran kablosu kontrol edildi',
                'Ekran kartı temizlendi',
                'BIOS ekran ayarları sıfırlandı'
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
            ],
            'Ağ Bağlantısı': [
                'Yazıcı IP ayarları yapılandırıldı',
                'Yazıcı sürücüleri güncellendi',
                'Ağ portları kontrol edildi',
                'Yazıcı ağ kartı resetlendi'
            ]
        },
        'Ağ Donanımı': {
            'Switch': [
                'Switch portları kontrol edildi',
                'Switch firmware güncellendi',
                'Port yapılandırması düzeltildi',
                'Switch resetlendi'
            ],
            'Router': [
                'Router ayarları kontrol edildi',
                'Router firmware güncellendi',
                'Router resetlendi',
                'Router portları test edildi'
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
            ],
            'Word': [
                'Word önbelleği temizlendi',
                'Word ayarları sıfırlandı',
                'Normal.dotm şablonu yenilendi',
                'Word eklentileri devre dışı bırakıldı'
            ]
        },
        'ERP': {
            'SAP': [
                'SAP GUI önbelleği temizlendi',
                'SAP oturum parametreleri sıfırlandı',
                'SAP GUI yeniden kuruldu',
                'Sistem bağlantı testi yapıldı'
            ],
            'Veritabanı': [
                'Veritabanı bağlantısı kontrol edildi',
                'Veritabanı önbelleği temizlendi',
                'Kullanıcı yetkileri güncellendi',
                'Veritabanı servisi yeniden başlatıldı'
            ]
        },
        'İşletim Sistemi': {
            'Windows': [
                'Windows güncellemeleri yapıldı',
                'Sistem dosyaları onarıldı',
                'Registry temizliği yapıldı',
                'Sistem geri yükleme yapıldı'
            ],
            'Sürücüler': [
                'Sürücüler güncellendi',
                'Sorunlu sürücüler kaldırılıp yeniden kuruldu',
                'Sürücü uyumluluk kontrolü yapıldı',
                'Sürücü önbelleği temizlendi'
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
        },
        'İnternet': {
            'Bağlantı': [
                'DNS ayarları güncellendi',
                'IP yapılandırması kontrol edildi',
                'Ağ kartı sıfırlandı',
                'Modem/router yeniden başlatıldı'
            ],
            'Performans': [
                'Hat kalitesi ölçüldü',
                'Ağ trafik analizi yapıldı',
                'Bandwidth optimizasyonu yapıldı',
                'Cache temizliği yapıldı'
            ]
        },
        'Ağ Erişimi': {
            'Paylaşım': [
                'Paylaşım izinleri kontrol edildi',
                'Grup politikaları güncellendi',
                'Ağ keşfi ayarları düzeltildi',
                'Güvenlik duvarı kuralları güncellendi'
            ],
            'Domain': [
                'Domain bağlantısı kontrol edildi',
                'GPO ayarları güncellendi',
                'Domain kullanıcı yetkileri kontrol edildi',
                'Domain controller bağlantısı test edildi'
            ]
        }
    }
}

# Problem detayları
problem_detaylari = {
    'PC Arıza': [
        'Bilgisayar neden Çalışmıyor',
        'Bilgisayar çok yavaş açılıyor ve fan sesi çok yüksek',
        'Bilgisayar sürekli donuyor ve yeniden başlıyor',
        'Ekran görüntüsü gelmiyor, sadece ses var',
        'Bilgisayar açılmıyor, güç ışığı yanmıyor',
        'Mavi ekran hatası veriyor'
    ],
    'Yazıcı Arıza': [
        'Yazıcı çok gürültülü çalışıyor',
        'Yazıcı kağıt sıkıştırıyor ve hata veriyor',
        'Çıktılar silik ve soluk çıkıyor',
        'Yazıcı ağda görünmüyor',
        'Yazıcı sürekli offline oluyor',
        'Yazıcı çıktı almıyor, hata veriyor'
    ],
    'Office': [
        'Serial Key Problemi',
        'Excel dosyası açılmıyor, sürekli kilitleniyor',
        'Outlook sürekli yanıt vermiyor hatası veriyor',
        'Word belgeleri kaydedilemiyor',
        'Excel makroları çalışmıyor',
        'Outlook e-posta göndermiyor'
    ],
    'ERP': [
        'SA P neden açılmıyor',
        'SAP sistemine giriş yapılamıyor',
        'SAP ekranı donuyor ve yanıt vermiyor',
        'SAP raporları açılmıyor',
        'SAP transaction hatası alıyorum',
        'SAP performansı çok yavaş'
    ],
    'VPN': [
        'VPN registration'
        'VPN bağlantısı kurulamıyor, timeout hatası',
        'VPN bağlantısı çok yavaş',
        'VPN sürekli kopuyor',
        'VPN client açılmıyor',
        'VPN authentication hatası'
    ],
    'İnternet': [
        'Şifre istiyor',
        'İnternet bağlantısı yok',
        'İnternet çok yavaş',
        'Web sayfaları açılmıyor',
        'DNS hatası alıyorum',
        'İnternet sürekli kesiliyor'
    ],
    'Ağ Erişimi': [
        'username ve password hatası',
        'Paylaşımlı klasörlere erişilemiyor',
        'Domain oturumu açılmıyor',
        'Ağ yazıcılarına erişilemiyor',
        'Ağ sürücüleri bağlanmıyor',
        'Uzak masaüstü bağlantısı kurulamıyor'
    ]
}

def get_solution_detail(kategori, alt_kategori, problem_tipi):
    try:
        cozumler = cozum_detaylari[kategori][alt_kategori][problem_tipi]
        return random.choice(cozumler)
    except KeyError:
        return "Standart prosedür uygulandı"

def drop_existing_table(cursor):
    cursor.execute("""
    IF OBJECT_ID('dbo.Tickets', 'U') IS NOT NULL 
        DROP TABLE dbo.Tickets
    """)

def create_tickets_table(cursor):
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
        PRIMARY KEY ([Ticket_ID]),
        [Musteri_ID] INT,
        [Model] NVARCHAR(50)
    )
    """)

def initialize_database(cursor, conn):
    drop_existing_table(cursor)
    conn.commit()
    print("Eski tablo silindi.")
    
    create_tickets_table(cursor)
    print("Yeni tablo oluşturuldu.")

# Müşteri ID'leri için basit bir liste
musteri_idleri = list(range(1001, 1010))  # 500 farklı müşteri

# Kategori bazlı modeller
model_listesi = {
    'PC Arıza': [
        'Dell Latitude 5520', 'HP EliteBook 840', 'Lenovo ThinkPad T14', 
        'Dell Precision 5560', 'HP ProBook 450', 'Asus ExpertBook B9'
    ],
    'Yazıcı Arıza': [
        'HP LaserJet Pro M404', 'Canon iR2625i', 'Xerox WorkCentre 6515',
        'Brother MFC-L8900CDW', 'Epson WorkForce Pro', 'Lexmark MC3326i'
    ],
    'Ağ Donanımı': [
        'Cisco Catalyst 2960', 'HP Aruba 2530', 'Juniper EX2300',
        'Dell PowerSwitch N1524', 'TP-Link TL-SG3428', 'Ubiquiti UniFi Switch'
    ]
}

def generate_ticket_data(baslangic_tarih, bitis_tarih, TOPLAM_KAYIT, cursor, conn):
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

        # Müşteri ID'si ata
        musteri_id = random.choice(musteri_idleri)
        
        # Alt kategoriye göre model seç
        model = ''  # Boş string ile başlat
        if alt_kategori in model_listesi:
            model = random.choice(model_listesi[alt_kategori])
        elif kategori == 'Yazılım':
            model = f'Software v{random.randint(1, 5)}.{random.randint(0, 9)}'
        elif kategori == 'Ağ':
            model = f'Network Device v{random.randint(1, 3)}'

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
            Yapilan_Islem, Kullanilan_Arac, Root_Cause,
            Musteri_ID, Model
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_id, bolge, oncelik, kategori, alt_kategori,
            teknisyen, teknisyen_seviye, olusturma_tarihi,
            atama_tarihi, cozum_tarihi, is_gununde,
            mesai_saatinde, hedef_atama, gercek_atama,
            hedef_cozum, gercek_cozum, atama_sla, cozum_sla,
            memnuniyet, problem, cozum, yapilan_islem,
            kullanilan_arac, root_cause, musteri_id, model
        ))

        if i % 1000 == 0:
            print(f"{i} adet ticket oluşturuldu ({(i/TOPLAM_KAYIT)*100:.1f}%)")
            conn.commit()
    
    conn.commit()

def initialize_test_data():
    baslangic_tarih = datetime(2023, 1, 1)
    bitis_tarih = datetime(2024, 1, 31)
    TOPLAM_KAYIT = 500000
    return baslangic_tarih, bitis_tarih, TOPLAM_KAYIT

def test_verisi_olustur():
    conn = pyodbc.connect('DRIVER={SQL Server};SERVER=DESKTOP-6QR83E3\\UGURMSSQL;DATABASE=FSM_Tickets;UID=usesen;PWD=usesen')
    cursor = conn.cursor()

    try:
        initialize_database(cursor, conn)
        baslangic_tarih, bitis_tarih, TOPLAM_KAYIT = initialize_test_data()
        generate_ticket_data(baslangic_tarih, bitis_tarih, TOPLAM_KAYIT, cursor, conn)
        print(f"Toplam {TOPLAM_KAYIT} adet ticket başarıyla oluşturuldu.")

    except Exception as e:
        print("Hata:", e)
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    test_verisi_olustur()