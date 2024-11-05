import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import create_engine, text
import re
import json
import os
import traceback

# Sabit listeler
LOCATIONS = [
    '3. kat',
    '4. kat',
    '5. kat',
    'toplantı odası',
    'ofis',
    'yemekhane',
    'lobi',
    'sistem odası',
    'arşiv',
    'uzaktan çalışma'
]

class NLPEngine:
    def __init__(self):
        self.engine = None
        self.df = None
        self.vectorizer = None
        self.model = None
        self._category_cache = {}
        self._initialized = False
        self.min_similarity = 0.3  # Minimum benzerlik eşiği
        self.location_weight = 0.2  # Konum ağırlığı
        
    def initialize(self):
        """Initialize the NLP engine if not already initialized"""
        if self._initialized:
            return
            
        try:
            self._setup_components()
            self._initialized = True
            
        except Exception as e:
            print(f"❌ Başlatma hatas: {str(e)}")
            traceback.print_exc()
            
    def _setup_components(self):
        """Set up all required components"""
        self._initialize_database()
        self._load_categories()
        print("📚 Ticket verileri yükleniyor...")
        self.load_data()
        
        if self.df is not None and len(self.df) > 0:
            print("🤖 Model eğitiliyor...")
            self.train_model()
            
        self._load_synonyms()

    def _initialize_database(self):
        """Initialize database connection"""
        self.engine = self._connect_to_database()
        print("✅ Veritabanı bağlantısı kuruldu")

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
            query = text("""
            SELECT Problem_Aciklamasi, Cozum_Aciklamasi, Teknisyen 
            FROM Tickets 
            WHERE Problem_Aciklamasi IS NOT NULL 
            AND Cozum_Aciklamasi IS NOT NULL
            """)
            
            with self.engine.connect() as conn:
                self.df = pd.read_sql(query, conn)
                print(f"✅ {len(self.df)} adet ticket yüklendi")
                
                if len(self.df) > 0:
                    self.df['processed_problem'] = self.df['Problem_Aciklamasi'].apply(
                        lambda x: self.preprocess_text(x)[0]
                    )
            
        except Exception as e:
            print(f"❌ Veri yükleme hatası: {str(e)}")
            traceback.print_exc()

    def _load_synonyms(self):
        """Eş anlamlı kelimeleri yükle"""
        try:
            query = "SELECT * FROM Kelime_Esanlamlilari"
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                for row in result:
                    self._category_cache[row.Kelime.lower()] = {
                        'kategori': row.Kategori,
                        'frekans': row.Kullanim_Frekansi,
                        'esanlamlilar': row.Es_Anlamli_Kelimeler.split(',') if row.Es_Anlamli_Kelimeler else []
                    }
            print("✅ Eş anlamlı kelimeler yüklendi")
        except Exception as e:
            print(f"❌ Eş anlamlı kelime yükleme hatası: {str(e)}")

    def preprocess_text(self, text):
        """Metin ön işleme geliştirmeleri"""
        if not text:
            return "", None
            
        text = text.lower()
        
        # Kategori eşleştirme puanlama sistemi
        category_scores = {
            'donanim': 0,
            'yazilim': 0,
            'ag': 0
        }
        
        # Her kategori için puan hesapla
        for category, info in self.categories.items():
            score = 0
            matches = [keyword for keyword in info['keywords'] if keyword in text]
            
            # Özel ağırlıklandırma kuralları
            for match in matches:
                base_score = 1
                # Yazılım uygulamaları için özel kural
                if category == 'yazilim' and match in ['outlook', 'teams', 'sap', 'excel', 'word']:
                    base_score = 2
                # Ağ terimleri için özel kural
                elif category == 'ag' and match in ['vpn', 'internet', 'bağlantı']:
                    base_score = 2
                    
                score += base_score
                
            category_scores[category] = score
        
        # En yüksek puanlı kategoriyi seç
        best_category = max(category_scores.items(), key=lambda x: x[1])
        selected_category = best_category[0] if best_category[1] > 0 else None
                
        return text, selected_category

    def calculate_similarity(self, text1, text2, category):
        """Geliştirilmiş benzerlik hesaplama"""
        base_similarity = self.vectorizer.transform([text1, text2])
        similarity = cosine_similarity(base_similarity)[0][1]
        
        # Kategori bazlı ağırlıklandırma
        weights = {
            'yazilim': {
                'sap': ['sap', 'gui', 'oturum', 'parametre'],
                'outlook': ['outlook', 'exchange', 'email', 'posta'],
                'teams': ['teams', 'microsoft', 'toplantı']
            },
            'ag': {
                'vpn': ['vpn', 'bağlantı', 'kopma', 'tunnel'],
                'internet': ['internet', 'yavaş', 'sayfa', 'dns'],
                'network': ['ağ', 'firewall', 'proxy', 'port']
            }
        }
        
        if category in weights:
            for subcategory, keywords in weights[category].items():
                if any(keyword in text1.lower() for keyword in keywords):
                    similarity += 0.1 * len([k for k in keywords if k in text2.lower()])  # Her eşleşen kelime için %10 bonus
        
        # Benzerlik skorunu normalize et
        return min(max(similarity, 0.3), 0.95)  # Minimum %30, Maximum %95

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
            # processed_problem artık bir tuple döndürdüğü için ilk eleman alalım
            all_problems = ' '.join([prob[0] if isinstance(prob, tuple) else prob 
                                   for prob in self.df['processed_problem'].fillna('')])
            
            words = all_problems.split()
            word_freq = pd.Series(words).value_counts()
            
            # En sık kullanılan kelimeleri kaydet
            self.common_words = word_freq[word_freq > len(self.df) * 0.01]
            
            print(f"✅ {len(self.common_words)} adet sık kullanılan kelime kalıbı bulundu")
            
        except Exception as e:
            print(f"Kalıp analizi hatası: {str(e)}")
            
    def _validate_dataframe(self):
        """Validate if dataframe exists and has data"""
        return self.df is not None and len(self.df) > 0

    def get_similar_tickets(self, problem):
        """Benzer ticketları bul"""
        processed_problem = self.preprocess_text(problem)
        category = self.categorize_problem(processed_problem)
        
        similar_tickets = []
        seen_solutions = set()
        
        for idx, row in self.df.iterrows():
            ticket_problem = row['Problem_Aciklamasi']
            solution = row['Cozum_Aciklamasi']
            
            # Çok kısa veya genel çözümleri atla
            if len(solution) < 15 or 'standart' in solution.lower():
                continue
                
            # Çözüm benzersizliğini kontrol et
            solution_key = solution.lower()[:50]
            if solution_key in seen_solutions:
                continue
                
            similarity = self.calculate_similarity(processed_problem, ticket_problem, category)
            
            if similarity >= 0.3:  # Minimum %30 benzerlik
                similar_tickets.append({
                    'Cozum_Aciklamasi': solution,
                    'Benzerlik_Skoru': round(similarity * 100, 2)
                })
                seen_solutions.add(solution_key)
                
            if len(similar_tickets) >= 4:
                break
        
        # Sonuçları benzerlik skoruna göre sırala
        return sorted(similar_tickets, key=lambda x: x['Benzerlik_Skoru'], reverse=True)
                
    def learn_synonyms(self, text1, text2, category=None):
        """Yeni eş anlamlı kelime çifti öğren"""
        try:
            # Metinleri ön işle
            text1 = self.preprocess_text(text1)
            text2 = self.preprocess_text(text2)
            
            # Veritabanına kaydet
            query = """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Synonyms')
            CREATE TABLE Synonyms (
                ID INT IDENTITY(1,1) PRIMARY KEY,
                Text1 NVARCHAR(100),
                Text2 NVARCHAR(100),
                Category NVARCHAR(50),
                CreatedDate DATETIME DEFAULT GETDATE()
            );

            INSERT INTO Synonyms (Text1, Text2, Category)
            VALUES (:text1, :text2, :category)
            """
            
            with self.engine.connect() as conn:
                conn.execute(text(query), 
                           {"text1": text1, "text2": text2, "category": category or 'Genel'})
                
            print(f"Yeni eş anlamlı kelimeler öğrenildi: {text1} = {text2}")
            
        except Exception as e:
            print(f"Eş anlamlı kelime öğrenme hatası: {str(e)}")
            
    def get_total_tickets(self):
        """Veritabanındaki toplam ticket sayısını döndür"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM Tickets"))
                return result.scalar()
        except Exception as e:
            print(f"Veritaban hatas: {str(e)}")
            return 0
            
    def _add_sample_ticket(self, device, issue, symptom):
        """Örnek ticket ekle"""
        try:
            query = """
            INSERT INTO Tickets (
                Problem_Aciklamasi, 
                Cozum_Aciklamasi,
                Teknisyen,
                Olusturma_Tarihi,
                Bolge,
                Oncelik
            ) VALUES (
                ?, ?, ?, GETDATE(), 'Merkez', 'Orta'
            )
            """
            
            problem = f"{device} {issue} - {symptom}"
            solution = f"{device} için genel kontroller yapıldı ve sorun giderildi"
            
            with self.engine.connect() as conn:
                conn.execute(text(query), [problem, solution, "Sistem"])
                conn.commit()
                
            print(f"✅ Örnek ticket eklendi: {problem}")
            
        except Exception as e:
            print(f"❌ Örnek ticket ekleme hatası: {str(e)}")
            
    def update_synonyms(self, problem, solution):
        """Eş anlamlı kelimeleri güncelle"""
        try:
            # Mevcut kelime ve frekansları al
            query = """
            SELECT Kelime, Kullanim_Frekansi 
            FROM Kelime_Esanlamlilari 
            WHERE Kelime = ? OR Kelime IN (
                SELECT value FROM STRING_SPLIT(?, ',')
            )
            """
            
            # Frekansı artr veya yeni kelime ekle
            upsert_query = """
            MERGE Kelime_Esanlamlilari AS target
            USING (SELECT @Kelime as Kelime) AS source
            ON target.Kelime = source.Kelime
            WHEN MATCHED THEN
                UPDATE SET 
                    Kullanim_Frekansi = Kullanim_Frekansi + 1,
                    Son_Kullanim = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (Kelime, Es_Anlamli_Kelimeler, Kategori, Kullanim_Frekansi, Son_Kullanim)
                VALUES (@Kelime, @Esanlamlilar, @Kategori, 1, GETDATE());
            """
            
            with self.engine.connect() as conn:
                # Her kelime için güncelleme yap
                for word in set(problem.lower().split() + solution.lower().split()):
                    conn.execute(text(upsert_query), {
                        'Kelime': word,
                        'Esanlamlilar': '',  # İlk başta boş
                        'Kategori': 'Belirlenmedi'  # İlk kategori
                    })
                    
            print("✅ Eş anlamlı kelimeler güncellendi")
            
        except Exception as e:
            print(f"❌ Eş anlamlı kelime güncelleme hatası: {str(e)}")
            
    def _load_categories(self):
        """Kategorileri yükle ve anahtar kelimeleri güncelle"""
        try:
            # Temel kategoriler ve anahtar kelimeler
            self.categories = {
                'donanim': {
                    'keywords': {
                        'yazici', 'printer', 'bilgisayar', 'pc', 'laptop', 
                        'ekran', 'monitor', 'fan', 'kağıt', 'çıktı',
                        'tambur', 'toner', 'bellek', 'ram', 'işlemci',
                        'fare', 'mouse', 'klavye', 'keyboard', 'donanım'
                    },
                    'solutions': set()
                },
                'yazilim': {
                    'keywords': {
                        'sap', 'outlook', 'word', 'excel', 'teams',
                        'windows', 'office', 'uygulama', 'program', 'yazılım',
                        'gui', 'email', 'posta', 'dosya', 'profil',
                        'login', 'giriş', 'şifre', 'password', 'hesap'
                    },
                    'solutions': set()
                },
                'ag': {
                    'keywords': {
                        'vpn', 'internet', 'ağ', 'network', 'bağlantı',
                        'wifi', 'kablosuz', 'ethernet', 'ip', 'dns',
                        'timeout', 'kopma', 'yavas', 'ping', 'firewall',
                        'erişim', 'access', 'proxy', 'uzak', 'remote'
                    },
                    'solutions': set()
                }
            }
            
            # Veritabanından çözümleri yükle
            with self.engine.connect() as conn:
                for kategori in self.categories:
                    query = text("""
                        SELECT Problem_Aciklamasi, Cozum_Aciklamasi 
                        FROM Tickets 
                        WHERE Kategori = :kategori
                    """)
                    
                    # Her sorgu için yeni bir transaction kullan
                    with conn.begin():
                        result = conn.execute(query, {'kategori': kategori})
                        solutions = [row.Cozum_Aciklamasi for row in result]
                        self.categories[kategori]['solutions'].update(solutions)
                        
                print(f"✅ {len(self.categories)} kategori yüklendi")
                
        except Exception as e:
            print(f"❌ Kategori yükleme hatası: {str(e)}")
            traceback.print_exc()
            
    def _initialize_test_categories(self):
        """Test için seed kategori verisi"""
        self.categories = {
            'donanim': {
                'keywords': [
                    'yazici', 'printer', 'bilgisayar', 'pc', 'laptop', 
                    'ekran', 'monitor', 'fan', 'kağıt', 'çıktı',
                    'tambur', 'toner', 'bellek', 'ram', 'işlemci'
                ],
                'solutions': set()  # Çözümler veritabanından gelecek
            },
            'yazilim': {
                'keywords': [
                    'sap', 'outlook', 'word', 'excel', 'teams',
                    'windows', 'office', 'uygulama', 'program', 'yazılım',
                    'gui', 'email', 'posta', 'dosya', 'profil'
                ],
                'solutions': set()
            },
            'ag': {
                'keywords': [
                    'vpn', 'internet', 'ağ', 'network', 'bağlantı',
                    'wifi', 'kablosuz', 'ethernet', 'ip', 'dns',
                    'timeout', 'kopma', 'yavas', 'ping', 'firewall'
                ],
                'solutions': set()
            }
        }

    def debug_category_matching(self, test_problem):
        """Kategori eşleştirme debug fonksiyonu"""
        print(f"\nTest Problemi: {test_problem}")
        
        text, category = self.preprocess_text(test_problem)
        print(f"İşlenmiş Metin: {text}")
        print(f"Tespit Edilen Kategori: {category}")
        
        # Eşleşen kelimeleri göster
        for cat, info in self.categories.items():
            if matches := [kw for kw in info['keywords'] if kw in text]:
                print(f"{cat.upper()} kategorisinde eşleşen kelimeler: {matches}")
            