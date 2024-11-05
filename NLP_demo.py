import pyodbc
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import nltk
import random

# NLTK kaynaklarını indir
print("NLTK kaynakları indiriliyor...")
nltk.download('punkt')
nltk.download('stopwords')
print("NLTK kaynakları indirildi.")

from nltk.corpus import stopwords

# Türkçe stop words'leri yükle
turkish_stop_words = set(stopwords.words('turkish'))

# Kategori ve alt kategori eşleştirmeleri
kategori_eslesmeleri = {
    'bilgisayar': ('Donanım', 'PC Arıza'),
    'pc': ('Donanım', 'PC Arıza'),
    'laptop': ('Donanım', 'PC Arıza'),
    'yazici': ('Donanım', 'Yazıcı Arıza'),
    'printer': ('Donanım', 'Yazıcı Arıza'),
    'excel': ('Yazılım', 'Office'),
    'word': ('Yazılım', 'Office'),
    'outlook': ('Yazılım', 'Office'),
    'office': ('Yazılım', 'Office'),
    'sap': ('Yazılım', 'ERP'),
    'vpn': ('Ağ', 'VPN'),
    'internet': ('Ağ', 'İnternet'),
    'ag': ('Ağ', 'Ağ Erişimi')
}

# Problem tipleri ve çözüm şablonları
cozum_sablonlari = {
    'Yavaşlık': [
        'Sistem kaynaklarının kontrolü',
        'Disk temizliği ve optimizasyon',
        'RAM temizliği',
        'Sürücü güncellemeleri'
    ],
    'Bağlantı': [
        'Ağ ayarlarının kontrolü',
        'DNS ayarlarının güncellenmesi',
        'VPN client yeniden başlatma',
        'Firewall kurallarının kontrolü'
    ],
    'Office': [
        'Office önbellek temizliği',
        'Office onarımı',
        'Profil yeniden oluşturma',
        'Office yeniden kurulumu'
    ]
}

def preprocess_text(text):
    if isinstance(text, str):
        # Küçük harfe çevir
        text = text.lower()
        
        # Türkçe karakter normalizasyonu
        text = text.replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u')\
                   .replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
        
        # Yazım hatalarını düzelt
        text = text.replace('outlok', 'outlook')\
                   .replace('ofis', 'office')\
                   .replace('sap gui', 'sapgui')
        
        # Noktalama işaretlerini kaldır
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Gereksiz kelimeleri kaldır
        stop_words = turkish_stop_words.union({
            've', 'ile', 'icin', 'tarafindan', 'yapildi', 
            'edildi', 'olusturuldu', 'kuruldu'
        })
        
        # Kelimelere ayır ve gereksizleri çıkar
        words = text.split()
        words = [word for word in words if word not in stop_words]
        
        return ' '.join(words)
    return ''

def determine_category(text):
    """Metne göre kategori ve alt kategori belirle"""
    processed_text = preprocess_text(text)
    for keyword, (kategori, alt_kategori) in kategori_eslesmeleri.items():
        if keyword in processed_text:
            return kategori, alt_kategori
    return 'Diğer', 'Genel'

def get_solution_template(problem_text):
    """Problem metnine göre çözüm şablonu öner"""
    processed_text = preprocess_text(problem_text)
    
    if any(word in processed_text for word in ['yavas', 'kasma', 'donma']):
        return random.choice(cozum_sablonlari['Yavaşlık'])
    elif any(word in processed_text for word in ['baglanti', 'vpn', 'internet']):
        return random.choice(cozum_sablonlari['Bağlantı'])
    elif any(word in processed_text for word in ['excel', 'word', 'outlook', 'office']):
        return random.choice(cozum_sablonlari['Office'])
    
    return "Standart prosedür uygulandı"

# SQL Server Bağlantısı
conn = pyodbc.connect('DRIVER={SQL Server};SERVER=DESKTOP-6QR83E3\\UGURMSSQL;DATABASE=FSM_Tickets;UID=usesen;PWD=usesen')

try:
    # Verileri çek
    query = """
    SELECT 
        Ticket_ID,
        Kategori,
        Alt_Kategori,
        Problem_Aciklamasi,
        Cozum_Aciklamasi,
        Yapilan_Islem,
        Kullanilan_Arac,
        Root_Cause,
        Teknisyen,
        Teknisyen_Seviye,
        Musteri_Memnuniyeti
    FROM Tickets
    WHERE Cozum_Aciklamasi IS NOT NULL
    """

    df = pd.read_sql(query, conn)
    print(f"Toplam {len(df)} ticket verisi yüklendi.")

    # Metinleri önişle
    print("Metinler önişleniyor...")
    df['processed_problem'] = df['Problem_Aciklamasi'].apply(preprocess_text)
    df['processed_solution'] = df['Cozum_Aciklamasi'].apply(preprocess_text)
    print("Önişleme tamamlandı.")

    def get_similar_tickets(new_problem, top_n=5):
        processed_problem = preprocess_text(new_problem)
        
        # Kategori belirle
        kategori, alt_kategori = determine_category(new_problem)
        
        # Çözüm şablonu al
        cozum_sablonu = get_solution_template(new_problem)
        
        # N-gram kullan
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            min_df=2,
            max_df=0.95
        )
        
        # Metin vektörlerini oluştur
        tfidf_matrix = vectorizer.fit_transform(df['processed_problem'])
        new_vector = vectorizer.transform([processed_problem])
        
        # Benzerlik hesapla
        similarity_scores = cosine_similarity(new_vector, tfidf_matrix)[0]
        
        # En benzer ticketları bul
        top_indices = similarity_scores.argsort()[-top_n:][::-1]
        top_scores = similarity_scores[top_indices]
        
        results = df.iloc[top_indices].copy()
        results['Benzerlik_Skoru'] = top_scores
        results['Tahmini_Kategori'] = kategori
        results['Tahmini_Alt_Kategori'] = alt_kategori
        results['Onerilen_Cozum'] = cozum_sablonu
        
        return results[['Ticket_ID', 'Kategori', 'Alt_Kategori', 
                       'Tahmini_Kategori', 'Tahmini_Alt_Kategori',
                       'Problem_Aciklamasi', 'Cozum_Aciklamasi',
                       'Onerilen_Cozum', 'Yapilan_Islem', 
                       'Kullanilan_Arac', 'Root_Cause',
                       'Teknisyen', 'Teknisyen_Seviye', 
                       'Musteri_Memnuniyeti', 'Benzerlik_Skoru']]

finally:
    conn.close()