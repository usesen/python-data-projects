import pandas as pd
import pyodbc
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os

def veri_cek():
    try:
        conn = pyodbc.connect('DRIVER={SQL Server};SERVER=DESKTOP-6QR83E3\\UGURMSSQL;DATABASE=FSM_Tickets;UID=usesen;PWD=usesen')
        
        query = """
        SELECT 
            Bolge,
            Oncelik,
            Kategori,
            Teknisyen,
            Olusturma_Tarihi,
            Atama_SLA_Uyumu,
            Cozum_SLA_Uyumu,
            Musteri_Memnuniyeti,
            Gercek_Cozum_Suresi_dk,
            Ticket_ID
        FROM Tickets
        WHERE Olusturma_Tarihi >= DATEADD(day, -30, GETDATE())  -- Son 30 günlük veri
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Veri çekme hatası: {str(e)}")
        return None

def analiz_yap(df):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    rapor_klasoru = os.path.join(script_dir, 'rapor_grafikleri')
    if not os.path.exists(rapor_klasoru):
        os.makedirs(rapor_klasoru)
    
    tarih = datetime.now().strftime('%Y%m%d')
    grafik_dosyalari = [
        f'{rapor_klasoru}/performans_{tarih}.png',
        f'{rapor_klasoru}/bolge_{tarih}.png',
        f'{rapor_klasoru}/teknisyen_{tarih}.png'
    ]
    
    # 1. SLA Performans Analizi
    plt.figure(figsize=(10, 6))
    sla_performans = pd.DataFrame({
        'Atama SLA': [df['Atama_SLA_Uyumu'].mean() * 100],
        'Çözüm SLA': [df['Cozum_SLA_Uyumu'].mean() * 100],
        'Müşteri Memnuniyeti': [df['Musteri_Memnuniyeti'].mean() * 100]
    })
    sla_performans.plot(kind='bar')
    plt.title('Genel Performans Analizi (%)')
    plt.tight_layout()
    dosya_adi = f'{rapor_klasoru}/performans_{tarih}.png'
    plt.savefig(dosya_adi)
    grafik_dosyalari.append(dosya_adi)
    plt.close()

    # 2. Bölge Bazlı Analiz
    plt.figure(figsize=(12, 6))
    bolge_analiz = df.groupby('Bolge').agg({
        'Bolge': 'count',
        'Cozum_SLA_Uyumu': 'mean',
        'Musteri_Memnuniyeti': 'mean'
    })
    bolge_analiz.plot(kind='bar')
    plt.title('Bölge Bazlı Performans')
    plt.tight_layout()
    dosya_adi = f'{rapor_klasoru}/bolge_{tarih}.png'
    plt.savefig(dosya_adi)
    grafik_dosyalari.append(dosya_adi)
    plt.close()

    # 3. Teknisyen Performans Analizi - Geliştirilmiş
    plt.figure(figsize=(15, 10))
    
    # Alt grafikler için figure oluştur
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    
    # 1. Ortalama Çözüm Süresi
    teknisyen_cozum_suresi = df.groupby('Teknisyen')['Gercek_Cozum_Suresi_dk'].mean().sort_values(ascending=True)
    teknisyen_cozum_suresi.plot(kind='barh', ax=ax1)
    ax1.set_title('Teknisyen Bazlı Ortalama Çözüm Süresi (dk)')
    ax1.set_xlabel('Dakika')
    
    # 2. Ticket Sayısı ve SLA Uyumu
    teknisyen_is_yuku = df.groupby('Teknisyen').agg({
        'Ticket_ID': 'count',
        'Cozum_SLA_Uyumu': 'mean'
    }).sort_values('Ticket_ID', ascending=True)
    
    teknisyen_is_yuku['Ticket_ID'].plot(kind='barh', ax=ax2)
    ax2.set_title('Teknisyen Bazlı Ticket Sayısı')
    
    # 3. Öncelik Dağılımı
    oncelik_dagilimi = pd.crosstab(df['Teknisyen'], df['Oncelik'])
    oncelik_dagilimi.plot(kind='bar', stacked=True, ax=ax3)
    ax3.set_title('Teknisyen Bazlı Öncelik Dağılımı')
    ax3.tick_params(axis='x', rotation=45)
    
    # 4. Müşteri Memnuniyeti ve SLA Uyumu Karşılaştırması
    teknisyen_performans = df.groupby('Teknisyen').agg({
        'Musteri_Memnuniyeti': 'mean',
        'Cozum_SLA_Uyumu': 'mean',
        'Atama_SLA_Uyumu': 'mean'
    }) * 100
    
    teknisyen_performans.plot(kind='bar', ax=ax4)
    ax4.set_title('Teknisyen Performans Metrikleri (%)')
    ax4.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    dosya_adi = f'{rapor_klasoru}/teknisyen_detay_{tarih}.png'
    plt.savefig(dosya_adi)
    grafik_dosyalari.append(dosya_adi)
    plt.close()

    # Şehir/Bölge Analizi
    plt.figure(figsize=(15, 10))
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))

    # 1. Şehir bazlı ticket dağılımı
    sehir_dagilim = df['Bolge'].value_counts()
    sehir_dagilim.plot(kind='pie', autopct='%1.1f%%', ax=ax1)
    ax1.set_title('Şehirlere Göre Ticket Dağılımı')

    # 2. Şehir bazlı ortalama çözüm süreleri
    sehir_cozum = df.groupby('Bolge')['Gercek_Cozum_Suresi_dk'].mean().sort_values(ascending=True)
    sehir_cozum.plot(kind='barh', ax=ax2)
    ax2.set_title('Şehir Bazlı Ortalama Çözüm Süresi (dk)')
    ax2.set_xlabel('Dakika')

    # 3. Şehir ve öncelik dağılımı
    sehir_oncelik = pd.crosstab(df['Bolge'], df['Oncelik'])
    sehir_oncelik.plot(kind='bar', stacked=True, ax=ax3)
    ax3.set_title('Şehir Bazlı Öncelik Dağılımı')
    ax3.tick_params(axis='x', rotation=45)

    # 4. Şehir performans metrikleri
    sehir_performans = df.groupby('Bolge').agg({
        'Musteri_Memnuniyeti': 'mean',
        'Cozum_SLA_Uyumu': 'mean',
        'Atama_SLA_Uyumu': 'mean'
    }) * 100
    sehir_performans.plot(kind='bar', ax=ax4)
    ax4.set_title('Şehir Performans Metrikleri (%)')
    ax4.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    dosya_adi = f'{rapor_klasoru}/sehir_analiz_{tarih}.png'
    plt.savefig(dosya_adi)
    grafik_dosyalari.append(dosya_adi)
    plt.close()

    # Teknisyen özeti oluştur
    teknisyen_ozet = df.groupby('Teknisyen').agg({
        'Ticket_ID': 'count',
        'Gercek_Cozum_Suresi_dk': 'mean',
        'Musteri_Memnuniyeti': lambda x: (x.mean() * 100),
        'Cozum_SLA_Uyumu': lambda x: (x.mean() * 100)
    }).round(2)

    # Şehir özeti oluştur
    sehir_ozet = df.groupby('Bolge').agg({
        'Ticket_ID': 'count',
        'Gercek_Cozum_Suresi_dk': 'mean',
        'Musteri_Memnuniyeti': lambda x: (x.mean() * 100),
        'Cozum_SLA_Uyumu': lambda x: (x.mean() * 100)
    }).round(2)

    return grafik_dosyalari, sla_performans, teknisyen_ozet, sehir_ozet

def mail_gonder(grafik_dosyalari, sla_performans, teknisyen_ozet, sehir_ozet):
    print("Mail gönderme işlemi başlatılıyor...")
    
    sender_email = "info@crestafer.com"
    sender_password = "i#Sb8!N0"
    receiver_email = "admin@crestafer.com"

    try:
        msg = MIMEMultipart()
        msg['Subject'] = f'FSM Ticket Analiz Raporu - {datetime.now().strftime("%d.%m.%Y")}'
        msg['From'] = sender_email
        msg['To'] = receiver_email

        html = f"""
        <html>
            <body>
                <h2>FSM Ticket Sistemi Günlük Rapor</h2>
                <h3>Genel Performans Özeti:</h3>
                <ul>
                    <li>Atama SLA Uyumu: {sla_performans['Atama SLA'][0]:.2f}%</li>
                    <li>Çözüm SLA Uyumu: {sla_performans['Çözüm SLA'][0]:.2f}%</li>
                    <li>Müşteri Memnuniyeti: {sla_performans['Müşteri Memnuniyeti'][0]:.2f}%</li>
                </ul>
                
                <h3>Şehir Bazlı Performans Özeti:</h3>
                {sehir_ozet.to_html()}
                
                <h3>Teknisyen Performans Özeti:</h3>
                {teknisyen_ozet.to_html()}
                
                <p>Detaylı grafikler ekte yer almaktadır.</p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html, 'html'))

        print("Grafikler ekleniyor...")
        for dosya in grafik_dosyalari:
            print(f"Eklenen dosya: {dosya}")
            with open(dosya, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(dosya))
                msg.attach(img)

        with smtplib.SMTP('srvc166.turhost.com', 995) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            
        print("Mail başarıyla gönderildi!")

    except Exception as e:
        print(f"Mail gönderme hatası: {str(e)}")
        print(f"Hata detayı: {type(e).__name__}")
        import traceback
        print(traceback.format_exc())

def main():
    # Veriyi çek
    df = veri_cek()
    if df is not None:
        # Analiz yap ve grafikleri oluştur
        grafik_dosyalari, sla_performans, teknisyen_ozet, sehir_ozet = analiz_yap(df)
        # Mail gönder
        mail_gonder(grafik_dosyalari, sla_performans, teknisyen_ozet, sehir_ozet)

if __name__ == "__main__":
    main()
    
    
    