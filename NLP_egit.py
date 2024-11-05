import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine, text
import pickle
import os
from datetime import datetime
from gensim.models import Word2Vec, FastText
from transformers import AutoTokenizer, AutoModel
from TurkishStemmer import TurkishStemmer
import torch
from nltk.tokenize import word_tokenize
import nltk
import re
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

class NLPTrainer:
    def __init__(self):
        self.engine = None
        self.df = None
        self.vectorizer = None
        self.model_path = "models"
        self.categories = ['donanim', 'yazilim', 'ag']
        self.word2vec_model = None
        self.fasttext_model = None
        self.bert_model = None
        self.bert_tokenizer = None
        self.stemmer = TurkishStemmer()
        
        try:
            nltk.download('punkt', quiet=True, raise_on_error=True)
            nltk.download('punkt_tab', quiet=True, raise_on_error=True)
            
            # BERT modelini yükle
            self.bert_tokenizer = AutoTokenizer.from_pretrained("dbmdz/bert-base-turkish-cased")
            self.bert_model = AutoModel.from_pretrained("dbmdz/bert-base-turkish-cased")
        except Exception as e:
            print(f"Model yükleme hatası: {str(e)}")

    def connect_database(self):
        """Veritabanı bağlantısı kur"""
        try:
            connection_string = "mssql+pyodbc://usesen:usesen@DESKTOP-6QR83E3\\UGURMSSQL/FSM_Tickets?driver=SQL+Server"
            self.engine = create_engine(connection_string)
            print("✅ Veritabanı bağlantısı kuruldu")
        except Exception as e:
            print(f"❌ Veritabanı bağlantı hatası: {str(e)}")
            
    def load_data(self):
        """Veritabanından eğitim verilerini ve eş anlamlı kelimeleri yükle"""
        try:
            with self.engine.connect() as conn:
                # Eş anlamlı kelimeleri çek
                synonyms_query = text("""
                    SELECT 
                        Kelime,
                        Es_Anlamli_Kelimeler as Esanlamlisi
                    FROM dbo.Kelime_Esanlamlilari
                """)
                
                self._load_tickets_data(conn)
                self._load_synonyms_data(conn, synonyms_query)
            
            self._analyze_data()
                
        except Exception as e:
            print(f"❌ Veri yükleme hatası: {str(e)}")
            self.synonyms_dict = {}

    def _load_tickets_data(self, conn):
        """Load tickets data from database"""
        tickets_query = text("""
            SELECT 
                Problem_Aciklamasi,
                Cozum_Aciklamasi,
                Kategori,
                Teknisyen
            FROM Tickets
        """)
        self.df = pd.read_sql(tickets_query, conn)
        print(f"✅ {len(self.df)} adet ticket yüklendi")
        
    def _load_synonyms_data(self, conn, query):
        """Load synonyms data from database"""
        self.synonyms_df = pd.read_sql(query, conn)
        print(f"✅ {len(self.synonyms_df)} adet eş anlamlı kelime yüklendi")
        
        # Eş anlamlı kelimeleri sözlüğe çevir
        self.synonyms_dict = {}
        for _, row in self.synonyms_df.iterrows():
            self.synonyms_dict[row['Kelime']] = row['Esanlamlisi']
        
    def _analyze_data(self):
        """Veri setini analiz et"""
        print("\n📊 Veri Analizi:")
        print(f"Toplam Ticket: {len(self.df)}")
        print("\nKategori Dağılımı:")
        print(self.df['Kategori'].value_counts())
        print("\nTeknisyen Dağılımı:")
        print(self.df['Teknisyen'].value_counts().head())
        
    def preprocess_text(self, text):
        """Metin ön işleme"""
        # Küçük harfe çevir
        text = text.lower()
        
        # Noktalama işaretlerini kaldır
        text = re.sub(r'[^\w\s]', '', text)
        
        # Stemming uygula
        words = text.split()
        stemmed_words = [self.stemmer.stem(word) for word in words]
        
        return ' '.join(stemmed_words)

    def generate_synonyms(self):
        """Problem açıklamalarından eş anlamlı kelimeleri öğren ve kaydet"""
        try:
            print("\n🔍 Eş anlamlı kelimeler öğreniliyor...")
            
            # Metinleri temizle ve tokenize et
            sentences = []
            
            print("Metin ön işleme yapılıyor...")
            for text in tqdm(self.df['Problem_Aciklamasi'].fillna('')):
                # Her cümleyi kelimelere ayır
                if words := word_tokenize(self.preprocess_text(text)):
                    sentences.append(words)

            if not sentences:
                print("❌ İşlenecek cümle bulunamadı")
                return

            print(f"✅ {len(sentences)} cümle işlendi")
            print(f"Örnek cümle: {sentences[0]}")

            # Word2Vec modelini eğit
            print("\nWord2Vec modeli eğitiliyor...")
            self.word2vec_model = Word2Vec(
                sentences=sentences,
                vector_size=100,
                window=5,
                min_count=2,  # En az 2 kez geçen kelimeler
                workers=4,
                epochs=10  # Epoch sayısını artır
            )
            
            # FastText modelini eğit
            print("\nFastText modeli eğitiliyor...")
            self.fasttext_model = FastText(
                sentences=sentences,
                vector_size=100,
                window=5,
                min_count=2,
                workers=4,
                epochs=10
            )

            # Her kategori için işlem yap
            for kategori in self.categories:
                print(f"\n{kategori.upper()} kategorisi işleniyor...")
                kategori_texts = self.df[self.df['Kategori'].str.lower() == kategori]['Problem_Aciklamasi']
                
                # Preprocess and filter empty texts
                processed_texts = [self.preprocess_text(text) for text in kategori_texts if text and isinstance(text, str)]
                
                if not processed_texts:
                    print(f"⚠️ {kategori} kategorisinde işlenecek metin bulunamadı")
                    continue
                
                # TF-IDF with non-empty texts
                vectorizer = TfidfVectorizer(max_features=100, min_df=2)  # Add min_df parameter
                tfidf_matrix = vectorizer.fit_transform(processed_texts)
                feature_names = vectorizer.get_feature_names_out()
                
                # Her kelime için benzer kelimeleri bul
                for word in tqdm(feature_names, desc="Kelimeler işleniyor"):
                    if synonyms := self._find_word_synonyms(word, kategori):
                        self._save_synonym(word, ','.join(synonyms), kategori)
                        print(f"✅ {word} -> {synonyms}")

            print("\n✅ Eş anlamlı kelimeler öğrenildi ve kaydedildi")
            
        except Exception as e:
            print(f"❌ Eş anlamlı kelime öğrenme hatası: {str(e)}")
            raise  # Hatanın detayını görmek için

    def _get_bert_embeddings(self, texts):
        """BERT embeddings hesapla"""
        embeddings = []
        
        with torch.no_grad():
            for text in tqdm(texts, desc="BERT embeddings hesaplanıyor"):
                inputs = self.bert_tokenizer(text, return_tensors="pt", padding=True, truncation=True)
                outputs = self.bert_model(**inputs)
                embeddings.append(outputs.last_hidden_state.mean(dim=1).squeeze().numpy())
        
        return np.array(embeddings)

    def _find_word_synonyms(self, word, category):
        """Bir kelime için tüm modelleri kullanarak eş anlamlıları bul"""
        synonyms = set()
        
        # Debug için print ekleyelim
        print(f"Aranan kelime: {word}")
        
        # Word2Vec benzerliği
        try:
            similar_words = self.word2vec_model.wv.most_similar(word, topn=3)
            print(f"Word2Vec benzer kelimeler: {similar_words}")
            synonyms.update([w for w, s in similar_words if s > 0.6])
        except Exception as e:
            print(f"Word2Vec hatası: {str(e)}")
        
        # FastText benzerliği
        try:
            similar_words = self.fasttext_model.wv.most_similar(word, topn=3)
            print(f"FastText benzer kelimeler: {similar_words}")
            synonyms.update([w for w, s in similar_words if s > 0.6])
        except Exception as e:
            print(f"FastText hatası: {str(e)}")
        
        print(f"Bulunan eş anlamlılar: {list(synonyms)}\n")
        return list(synonyms)

    def preprocess_data(self):
        """Verileri ön işleme"""
        try:
            print("\n🔄 Veri ön işleme başladı...")
            
            # Eksik değerleri temizle
            self.df = self.df.dropna(subset=['Problem_Aciklamasi', 'Cozum_Aciklamasi'])
            
            print("Metinler işleniyor...")
            # Metinleri işle
            tqdm.pandas()
            self.df['processed_problem'] = self.df['Problem_Aciklamasi'].progress_apply(self.preprocess_text)
            self.df['processed_solution'] = self.df['Cozum_Aciklamasi'].progress_apply(self.preprocess_text)
            
            # Eş anlamlı kelime değişimi - daha verimli hale getirildi
            print("Eş anlamlı kelimeler uygulanıyor...")
            def apply_synonyms(row):
                text = row['processed_problem']
                category = row['Kategori'].lower()
                words = text.split()
                
                for word in words:
                    if similar := self._find_word_synonyms(word, category):
                        text = text.replace(word, similar[0])
                return text
            
            self.df['processed_problem'] = self.df.progress_apply(apply_synonyms, axis=1)
            
            print("✅ Veri ön işleme tamamlandı")
            
        except Exception as e:
            print(f"❌ Veri ön işleme hatası: {str(e)}")

    def train_model(self):
        """TF-IDF modelini eğit"""
        try:
            if self.df is None or len(self.df) == 0:
                print("❌ Eğitim için veri bulunamadı")
                return

            print("\n🤖 Model eğitimi başladı...")
            
            # TF-IDF Vectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 2),
                stop_words=['ve', 'veya', 'ile', 'için']
            )
            
            # Modeli eğit
            X = self.vectorizer.fit_transform(self.df['processed_problem'])
            
            print(f"✅ Model eğitildi: {X.shape[0]} örnek, {X.shape[1]} özellik")
            
            # Modeli kaydet
            self._save_model()
            
        except Exception as e:
            print(f"❌ Model eğitim hatası: {str(e)}")
            
    def _save_model(self):
        """Eğitilen modeli kaydet"""
        try:
            if not os.path.exists(self.model_path):
                os.makedirs(self.model_path)
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Vectorizer'ı kaydet
            vectorizer_path = f"{self.model_path}/vectorizer_{timestamp}.pkl"
            with open(vectorizer_path, 'wb') as f:
                pickle.dump(self.vectorizer, f)
                
            # Eğitim verilerini kaydet
            data_path = f"{self.model_path}/training_data_{timestamp}.pkl"
            with open(data_path, 'wb') as f:
                pickle.dump({
                    'problems': self.df['processed_problem'].tolist(),
                    'solutions': self.df['processed_solution'].tolist(),
                    'categories': self.df['Kategori'].tolist()
                }, f)
                
            print(f"✅ Model kaydedildi: {vectorizer_path}")
            
        except Exception as e:
            print(f"❌ Model kaydetme hatası: {str(e)}")
            
    def test_model(self, test_problems):
        """Modeli test et"""
        if not (self.vectorizer and hasattr(self.vectorizer, 'vocabulary_')):
            print("❌ Model henüz eğitilmemiş")
            return

        print("\n🧪 Model testi başladı...")
        
        for problem in test_problems:
            print(f"\n📝 Test Problemi: {problem}")
            
            # Problemi vektörize et
            problem_vec = self.vectorizer.transform([problem.lower()])
            
            # Benzerlik hesapla
            similarities = (problem_vec * self.vectorizer.transform(
                self.df['processed_problem']
            ).T).toarray()[0]
            
            # En benzer 3 çözümü bul
            most_similar = similarities.argsort()[-3:][::-1]
            
            print("\n💡 Benzer Çözümler:")
            for idx in most_similar:
                print(f"- {self.df.iloc[idx]['Cozum_Aciklamasi']}")
                print(f"  Benzerlik: {similarities[idx]:.2%}")
                print(f"  Kategori: {self.df.iloc[idx]['Kategori']}")
                print()

    def _truncate_synonyms_table(self):
        """Truncate the synonyms table"""
        with self.engine.connect() as conn:
            truncate_query = text("TRUNCATE TABLE dbo.Kelime_Esanlamlilari")
            conn.execute(truncate_query)
            conn.commit()
            print("✅ Kelime_Esanlamlilari tablosu temizlendi")

    def _save_synonym(self, kelime, esanlamlisi, kategori):
        """Eş anlamlı kelimeyi veritabanına kaydet"""
        try:
            with self.engine.connect() as conn:
                query = text("""
                    INSERT INTO dbo.Kelime_Esanlamlilari 
                    (Kelime, Es_Anlamli_Kelimeler, Kategori, Kullanim_Frekansi, Son_Kullanim)
                    VALUES (:kelime, :esanlamlisi, :kategori, 1, GETDATE())
                """)
                conn.execute(query, {
                    'kelime': kelime,
                    'esanlamlisi': esanlamlisi,
                    'kategori': kategori
                })
                conn.commit()
        except Exception as e:
            print(f"❌ Kelime kaydetme hatası: {str(e)}")

    def find_similar_words(self, word, category=None):
        """Bir kelime için eş anlamlıları bul"""
        try:
            similar_words = []
            
            # Word2Vec benzerliği
            if self.word2vec_model and word in self.word2vec_model.wv:
                similar_words = [w for w, s in self.word2vec_model.wv.most_similar(word, topn=3) if s > 0.6]
            
            # Kategori bazlı filtreleme
            if category:
                with self.engine.connect() as conn:
                    query = text("""
                        SELECT Es_Anlamli_Kelimeler
                        FROM dbo.Kelime_Esanlamlilari
                        WHERE Kategori = :kategori AND Kelime = :kelime
                    """)
                    result = conn.execute(query, {'kategori': category, 'kelime': word}).fetchone()
                    if result and result[0]:
                        similar_words.extend(result[0].split(','))
            
            return list(set(similar_words))  # Tekrarları kaldır
            
        except Exception as e:
            print(f"❌ Benzer kelime bulma hatası: {str(e)}")
            return []

def main():
    trainer = NLPTrainer()
    
    # Veritabanı bağlantısı
    trainer.connect_database()
    
    # Veri yükleme
    trainer.load_data()
    
    # Eş anlamlıları öğren (önce modelleri eğit)
    print("\n1. Eş anlamlı kelimeler öğreniliyor...")
    trainer._truncate_synonyms_table()
    trainer.generate_synonyms()
    
    # Veri ön işleme ve model eğitimi
    print("\n2. Veri ön işleme yapılıyor...")
    trainer.preprocess_data()
    
    print("\n3. Model eğitiliyor...")
    trainer.train_model()
    
    # Test
    test_problems = [
        "Outlook açılmıyor ve e-posta gönderemiyor",
        "SAP sistemine giriş yapılamıyor, ekran donuyor",
        "VPN bağlantısı sürekli kopuyor",
        "İnternet çok yavaş, sayfalara giremiyorum"
    ]
    
    trainer.test_model(test_problems)

if __name__ == "__main__":
    main() 