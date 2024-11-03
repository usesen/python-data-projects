import pandas as pd
import pyodbc  # SQL Server için
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import schedule
import time
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

def veri_cek():
    # SQL Server Bağlantısı
    conn = pyodbc.connect(
        'DRIVER={SQL Server};'
        'SERVER=DESKTOP-6QR83E3\\UGURMSSQL;'
        'DATABASE=FSM_Tickets;'
        'UID=usesen;'
        'PWD=usesen'
    )
    
    # Veriyi çek
    query = """
    SELECT t.TicketID, t.OlusturmaTarihi, t.CozumTarihi,
           t.Oncelik, t.Bolge, t.Teknisyen,
           t.SLAUyum, t.MusteriMemnuniyeti
    FROM Tickets t
    WHERE t.OlusturmaTarihi >= DATEADD(day, -30, GETDATE())
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def analiz_yap(df):
    # Mevcut analizler
    sla_performans = df.groupby('Bolge')['SLAUyum'].mean()
    teknisyen_performans = df.groupby('Teknisyen').agg({
        'TicketID': 'count',
        'SLAUyum': 'mean',
        'MusteriMemnuniyeti': 'mean'
    })
    
    # Yeni analizler ekleniyor
    # Çözüm süresi hesaplama
    df['CozumSuresi'] = (pd.to_datetime(df['CozumTarihi']) - 
                        pd.to_datetime(df['OlusturmaTarihi'])).dt.total_seconds() / 3600  # Saat cinsinden
    
    # Bölge bazlı ortalama çözüm süreleri
    bolge_cozum_suresi = df.groupby('Bolge')['CozumSuresi'].agg(['mean', 'min', 'max'])
    
    # Öncelik seviyesine göre SLA uyum analizi
    oncelik_sla = df.groupby('Oncelik')['SLAUyum'].mean()
    
    # SLA tahmin modeli
    def sla_tahmin_modeli(data):
        # Kategorik değişkenleri dönüştür
        data_model = pd.get_dummies(data[['Bolge', 'Oncelik', 'Teknisyen']])
        data_model['CozumSuresi'] = data['CozumSuresi']
        
        # Hedef değişken
        y = data['SLAUyum']
        
        # Eğitim ve test verisi ayırma
        X_train, X_test, y_train, y_test = train_test_split(data_model, y, test_size=0.2)
        
        # Model eğitimi
        model = RandomForestClassifier(n_estimators=100)
        model.fit(X_train, y_train)
        
        # Model performansı
        y_pred = model.predict(X_test)
        model_performans = classification_report(y_test, y_pred)
        
        return model, model_performans
    
    # Model eğitimi
    model, model_performans = sla_tahmin_modeli(df)
    
    kritik_durumlar = df[df['SLAUyum'] < 0.9]  # SLA < %90
    
    return {
        'sla': sla_performans,
        'teknisyen': teknisyen_performans,
        'kritik': kritik_durumlar,
        'bolge_cozum_suresi': bolge_cozum_suresi,
        'oncelik_sla': oncelik_sla,
        'model_performans': model_performans,
        'model': model
    }

def rapor_olustur(analizler):
    with pd.ExcelWriter('FSM_Rapor.xlsx') as writer:
        analizler['sla'].to_excel(writer, sheet_name='SLA_Performans')
        analizler['teknisyen'].to_excel(writer, sheet_name='Teknisyen_Performans')
        analizler['kritik'].to_excel(writer, sheet_name='Kritik_Durumlar')
        analizler['bolge_cozum_suresi'].to_excel(writer, sheet_name='Bolge_Cozum_Sureleri')
        analizler['oncelik_sla'].to_excel(writer, sheet_name='Oncelik_SLA_Analizi')
        
        # Model performans raporu
        pd.DataFrame({'Model_Performans': [analizler['model_performans']]}).to_excel(
            writer, sheet_name='Model_Performans')
    
    return 'FSM_Rapor.xlsx'

def mail_gonder(dosya_adi, alicilar):
    # Mail ayarları
    sender = "info@crestafer.com"
    password = "i#Sb8!N0"
    
    # Mail içeriği
    msg = MIMEMultipart()
    msg['Subject'] = 'FSM Günlük Performans Raporu'
    msg['From'] = sender
    msg['To'] = ', '.join(alicilar)
    
    # Mail metni
    body = """
    Merhaba,
    
    FSM günlük performans raporu ekte sunulmuştur.
    
    Önemli Noktalar:
    - SLA Uyum Oranı: {sla_oran}%
    - Kritik Ticket Sayısı: {kritik_sayi}
    - En İyi Performans: {en_iyi_bolge}
    
    Detaylı bilgi için ekteki Excel dosyasını inceleyebilirsiniz.
    
    İyi çalışmalar,
    FSM Sistem
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Excel dosyasını ekle
    with open(dosya_adi, 'rb') as f:
        excel = MIMEApplication(f.read(), _subtype='xlsx')
        excel.add_header('Content-Disposition', 'attachment', filename=dosya_adi)
        msg.attach(excel)
    
    # Maili gönder
    with smtplib.SMTP('srvc166.turhost.com', 995) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)

def gunluk_rapor():
    try:
        # Veriyi çek
        df = veri_cek()
        
        # Analiz yap
        analizler = analiz_yap(df)
        
        # Rapor oluştur
        dosya = rapor_olustur(analizler)
        
        # Mail gönder
        alicilar = [
            "info@crestafer.com",
            "admin@crestafer.com",
            "usesen@crestafer.com"
        ]
        mail_gonder(dosya, alicilar)
        
        print(f"Rapor başarıyla gönderildi: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
        # Hata durumunda bilgilendirme maili gönderilebilir

# Programı her gün saat 09:00'da çalıştır
schedule.every().day.at("09:00").do(gunluk_rapor)

# Sürekli çalışması için
while True:
    schedule.run_pending()
    time.sleep(60)
