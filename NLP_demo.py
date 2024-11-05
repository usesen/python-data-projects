import pyodbc
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import nltk

# NLTK kaynaklarını indir
print("NLTK kaynakları indiriliyor...")
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
print("NLTK kaynakları indirildi.")

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Türkçe stop words'leri yükle
turkish_stop_words = set(stopwords.words('turkish'))

# SQL Server Bağlantısı
conn = pyodbc.connect('DRIVER={SQL Server};SERVER=DESKTOP-6QR83E3\\UGURMSSQL;DATABASE=FSM_Tickets;UID=usesen;PWD=usesen')
cursor = conn.cursor()

try:
    # Veri durumunu kontrol edelim
    check_query = """
    SELECT COUNT(*) as BosKayitSayisi,
           COUNT(Problem_Aciklamasi) as Problem_Dolu,
           COUNT(Cozum_Aciklamasi) as Cozum_Dolu,
           COUNT(Yapilan_Islem) as Islemler_Dolu,
           COUNT(Root_Cause) as RootCause_Dolu
    FROM Tickets
    """
    cursor.execute(check_query)
    result = cursor.fetchone()
    print("Veri Durumu:", result)

    # Verileri çekelim
    query = """
    SELECT 
        Ticket_ID,
        Kategori,
        Alt_Kategori,
        Problem_Aciklamasi,
        Cozum_Aciklamasi,
        Yapilan_Islem,
        Kullanilan_Arac
    FROM Tickets
    WHERE Cozum_Aciklamasi IS NOT NULL
    """

    df = pd.read_sql(query, conn)
    print(f"Toplam {len(df)} ticket verisi yüklendi.")

    def preprocess_text(text):
        if isinstance(text, str):
            # Küçük harfe çevir
            text = text.lower()
            
            # Noktalama işaretlerini kaldır
            text = re.sub(r'[^\w\s]', ' ', text)
            
            # Boşlukları düzenle
            text = ' '.join(text.split())
            
            # Tokenize et
            words = text.split()  # Basit tokenization
            
            # Stop words'leri kaldır
            words = [word for word in words if word not in turkish_stop_words]
            
            return ' '.join(words)
        return ''

    # Metinleri önişle
    print("Metinler önişleniyor...")
    df['processed_problem'] = df['Problem_Aciklamasi'].apply(preprocess_text)
    df['processed_solution'] = df['Cozum_Aciklamasi'].apply(preprocess_text)
    print("Önişleme tamamlandı.")

    def get_similar_tickets(new_problem, top_n=5):
        processed_problem = preprocess_text(new_problem)
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(df['processed_problem'])
        new_vector = vectorizer.transform([processed_problem])
        similarity_scores = cosine_similarity(new_vector, tfidf_matrix)[0]
        
        # Skorlarla birlikte indeksleri al
        top_indices = similarity_scores.argsort()[-top_n:][::-1]
        top_scores = similarity_scores[top_indices]
        
        results = df.iloc[top_indices][['Ticket_ID', 'Kategori', 'Alt_Kategori', 
                                       'Problem_Aciklamasi', 'Cozum_Aciklamasi']]
        results['Benzerlik_Skoru'] = top_scores
        return results

 

finally:
    cursor.close()
    conn.close()