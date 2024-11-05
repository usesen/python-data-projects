import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import create_engine, text
import re
import json
import os

class NLPEngine:
    def __init__(self):
        self.engine = None
        self.df = None
        self.vectorizer = None
        self.model = None
        self._category_cache = {}
        self._initialized = False
        
    def initialize(self):
        """Initialize the NLP engine if not already initialized"""
        if not self._initialized:
            self._initialize_engine_and_data()
            self._initialized = True
            
    def _connect_to_database(self):
        """Veritabanı bağlantısı oluştur"""
        connection_string = "mssql+pyodbc://usesen:usesen@DESKTOP-6QR83E3\\UGURMSSQL/FSM_Tickets?driver=SQL+Server"
        return create_engine(connection_string)
        
    def _initialize_engine_and_data(self):
        """Initialize engine and load all required data"""
        self.engine = self._connect_to_database()
        
        print("Veriler yükleniyor...")
        self.load_data()
        
        print("Kelime kalıpları analiz ediliyor...")
        self.analyze_common_patterns()
        
        print("Model eğitiliyor...")
        self.train_model()
        
    def load_data(self):
        """Veritabanından verileri yükle"""
        try:
            query = """
            SELECT * FROM Tickets 
            WHERE Problem_Aciklamasi IS NOT NULL 
            AND Cozum_Aciklamasi IS NOT NULL
            """
            self.df = pd.read_sql(query, self.engine)
            
            # Metin ön işleme
            self.df['processed_problem'] = self.df['Problem_Aciklamasi'].apply(self.preprocess_text)
            
        except Exception as e:
            print(f"Veri yükleme hatası: {str(e)}")
            
    def _load_synonyms_cache(self):
        """Eş anlamlı kelimeleri önbelleğe al"""
        try:
            query = "SELECT Text1, Text2, Category FROM Synonyms"
            synonyms_df = pd.read_sql(query, self.engine)
            
            for _, row in synonyms_df.iterrows():
                self._category_cache[row['Text1']] = row['Category']
                self._category_cache[row['Text2']] = row['Category']
                
        except Exception as e:
            print(f"Eş anlamlı kelime yükleme hatası: {str(e)}")
            
    def preprocess_text(self, text):
        """Metin ön işleme"""
        if pd.isna(text): return ""
        
        # Küçük harfe çevir
        text = text.lower()
        
        # Gereksiz karakterleri temizle
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Fazla boşlukları temizle
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Eş anlamlı kelime değişimi
        words = text.split()
        processed_words = []
        
        for word in words:
            # Eş anlamlı kelime varsa değiştir
            if word in self._category_cache:
                processed_words.append(self._category_cache[word])
            else:
                processed_words.append(word)
                
        return ' '.join(processed_words)
        
    def train_model(self):
        """TF-IDF modelini eğit"""
        try:
            # Boş metin kontrolü
            valid_docs = self.df['processed_problem'].fillna('').astype(str)
            valid_docs = valid_docs[valid_docs.str.strip() != '']
            
            if len(valid_docs) == 0:
                print("UYARI: İşlenecek metin bulunamadı!")
                return
                
            # TF-IDF vektörizasyonu
            self.vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.99,
                strip_accents='unicode'
            )
            
            # Modeli eğit
            self.model = self.vectorizer.fit_transform(valid_docs)
            
        except Exception as e:
            print(f"Model eğitme hatası: {str(e)}")
            
    def analyze_common_patterns(self):
        """Sık kullanılan kelime kalıplarını analiz et"""
        try:
            all_problems = ' '.join(self.df['processed_problem'].fillna(''))
            words = all_problems.split()
            word_freq = pd.Series(words).value_counts()
            
            # En sık kullanılan kelimeleri kaydet
            self.common_words = word_freq[word_freq > len(self.df) * 0.01]
            
        except Exception as e:
            print(f"Kalıp analizi hatası: {str(e)}")
            
    def get_similar_tickets(self, problem, top_n=5):
        """Benzer ticketları bul ve JSON formatında döndür"""
        try:
            processed_problem = self.preprocess_text(problem)
            print(f"İşlenen problem: {processed_problem}")
            
            # Benzerlik hesapla
            problem_vector = self.vectorizer.transform([processed_problem])
            similarity_scores = cosine_similarity(self.model, problem_vector).flatten()
            
            final_results = []
            seen_solutions = set()
            
            sorted_indices = similarity_scores.argsort()[::-1]
            
            for idx in sorted_indices:
                if idx >= len(self.df):
                    continue
                    
                if len(final_results) >= top_n:
                    break
                    
                similarity = similarity_scores[idx]
                if similarity < 0.01:
                    continue
                    
                solution = self.df.iloc[idx]['Cozum_Aciklamasi']
                if solution not in seen_solutions:
                    seen_solutions.add(solution)
                    
                    result = {
                        'Problem_Aciklamasi': self.df.iloc[idx]['Problem_Aciklamasi'],
                        'Cozum_Aciklamasi': solution,
                        'Yapilan_Islemler': self.df.iloc[idx]['Yapilan_Islemler'] or '- ' + solution,
                        'Teknisyen': self.df.iloc[idx]['Teknisyen'],
                        'Benzerlik_Skoru': float(similarity * 100)
                    }
                    
                    # Boş string kontrolü
                    if not result['Yapilan_Islemler'].strip():
                        result['Yapilan_Islemler'] = '- ' + solution
                        
                    final_results.append(result)
            
            return final_results
            
        except Exception as e:
            print(f"Benzer ticket bulma hatası: {str(e)}")
            return []
            
    def learn_synonyms(self, text1, text2, category=None):
        """Yeni eş anlamlı kelime çifti öğren"""
        try:
            # Metinleri ön işle
            text1 = self.preprocess_text(text1)
            text2 = self.preprocess_text(text2)
            
            # Kelimeleri ayır
            words1 = set(text1.split())
            words2 = set(text2.split())
            
            # Kategoriyi belirle
            if category is None:
                # Metindeki kelimelere göre kategori tahmin et
                for word in words1.union(words2):
                    if word in self._category_cache:
                        category = self._category_cache[word]
                        break
                        
                category = category or 'Genel'
                
            # Veritabanına kaydet
            query = """
            INSERT INTO Synonyms (Text1, Text2, Category)
            VALUES (:text1, :text2, :category)
            """
            
            with self.engine.connect() as conn:
                conn.execute(text(query), 
                           {"text1": text1, "text2": text2, "category": category})
                
            # Önbelleği güncelle
            self._category_cache[text1] = category
            self._category_cache[text2] = category
            
        except Exception as e:
            print(f"Eş anlamlı kelime öğrenme hatası: {str(e)}") 