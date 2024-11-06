import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import create_engine, text
import traceback
from unidecode import unidecode
import re

class NLPEngine:
    def __init__(self):
        self.engine = None
        self.df = None
        self.vectorizer = None
        self.categories = None
        self.min_similarity = 0.3
        
    def initialize(self):
        """Sistemi başlat"""
        try:
            self._connect_database()
            self._load_data()
            self._setup_categories()
            self._train_model()
            print("✅ NLP Engine başarıyla başlatıldı")
        except Exception as e:
            print(f"❌ Başlatma hatası: {str(e)}")
            traceback.print_exc()
            
    def _connect_database(self):
        """Veritabanı bağlantısı kur"""
        connection_string = "mssql+pyodbc://usesen:usesen@DESKTOP-6QR83E3\\UGURMSSQL/FSM_Tickets?driver=SQL+Server"
        self.engine = create_engine(connection_string)
        print("✅ Veritaban bağlantısı kuruldu")
        
    def _load_data(self):
        """Ticket verilerini yükle"""
        query = text("""
            WITH RankedTickets AS (
                SELECT 
                    t.Ticket_ID as ticket_id,
                    t.Musteri_ID as customer_id,
                    t.Model as model,
                    t.Problem_Aciklamasi as problem_description,
                    t.Cozum_Aciklamasi as solution_description,
                    t.Kategori as kategori,
                    t.Alt_Kategori as alt_kategori,
                    ROW_NUMBER() OVER (PARTITION BY t.Problem_Aciklamasi ORDER BY t.Ticket_ID DESC) as rn
                FROM Tickets t
                WHERE t.Problem_Aciklamasi IS NOT NULL 
                AND t.Cozum_Aciklamasi IS NOT NULL
                AND t.Cozum_Aciklamasi != 'standart prosedur uygulandi'
                AND LEN(TRIM(t.Problem_Aciklamasi)) > 10
                AND LEN(TRIM(t.Cozum_Aciklamasi)) > 10
            )
            SELECT 
                ticket_id,
                customer_id,
                model,
                problem_description,
                solution_description,
                kategori,
                alt_kategori
            FROM RankedTickets
            WHERE rn = 1
            ORDER BY ticket_id DESC
        """)
        
        with self.engine.connect() as conn:
            result = conn.execute(query)
            self.df = pd.DataFrame(result.fetchall())
            print("\n=== Veri Yükleme Kontrolü ===")
            print(f"Toplam benzersiz kayıt: {len(self.df)}")
            print("Örnek problem-çözüm çiftleri:")
            sample_data = self.df.sample(n=3) if len(self.df) > 3 else self.df
            for _, row in sample_data.iterrows():
                print(f"\nProblem: {row['problem_description']}")
                print(f"Çözüm: {row['solution_description']}")

    def _setup_categories(self):
        """Kategorileri ayarla"""
        self.categories = {
            'donanim': {
                'keywords': {'bilgisayar', 'ekran', 'yazıcı', 'fare', 'klavye', 'monitör', 'printer'}
            },
            'yazilim': {
                'keywords': {'windows', 'office', 'excel', 'word', 'outlook', 'uygulama'}
            },
            'ag': {
                'keywords': {'internet', 'wifi', 'bağlantı', 'ağ', 'network', 'vpn'}
            }
        }
        
    def _train_model(self):
        """TF-IDF modelini eğit"""
        self.vectorizer = TfidfVectorizer()
        self.vectorizer.fit(self.df['problem_description'])
        print("✅ Model eğitimi tamamlandı")
        
    def _filter_by_model(self, model):
        """Modele göre ticketları filtrele"""
        filtered_df = self.df[self.df['model'] == model].copy()
        return None if filtered_df.empty else filtered_df

    def _get_filtered_tickets(self, model):
        """Get filtered tickets by model, returns empty list if no matches"""
        filtered_df = self._filter_by_model(model)
        return [] if filtered_df is None else filtered_df

    def _is_valid_dataframe(self, df):
        """Check if input is a valid DataFrame"""
        return isinstance(df, pd.DataFrame)

    def _validate_tickets(self, model):
        """Validate and return filtered tickets for given model"""
        filtered_df = self._get_filtered_tickets(model)
        return filtered_df if self._is_valid_dataframe(filtered_df) else None

    def _calculate_similarities(self, problem, filtered_df):
        """Calculate similarity scores between problem and filtered tickets"""
        problem_vector = self.vectorizer.transform([problem])
        all_vectors = self.vectorizer.transform(filtered_df['problem_description'])
        return cosine_similarity(problem_vector, all_vectors)[0]

    def _get_validated_tickets(self, model):
        """Model bazlı filtreleme yaparken daha esnek davran"""
        if not isinstance(model, str):
            return None

        # Model kategorilerini belirle
        software_models = ['Software', 'SAP', 'Network']
        hardware_models = ['HP', 'Xerox', 'Ubiquiti', 'Device']

        is_software = any(keyword.lower() in model.lower() for keyword in software_models)
        is_hardware = any(keyword.lower() in model.lower() for keyword in hardware_models)

        # Filtrelemeyi kategoriye göre yap
        if is_software:
            mask = self.df['model'].str.contains('|'.join(software_models), case=False, na=False)
        elif is_hardware:
            mask = self.df['model'].str.contains('|'.join(hardware_models), case=False, na=False)
        else:
            mask = self.df['model'].str.contains(model, case=False, na=False)

        return self.df[mask]

    def _calculate_relevance_score(self, problem_type, solution_type):
        """Çözüm ile problem tipinin uyumluluğunu kontrol et"""
        problem_keywords = {
            'SAP': ['sap', 'transaction', 'module'],
            'VPN': ['vpn', 'bağlantı', 'connection'],
            'NETWORK': ['internet', 'ağ', 'network', 'dns'],
            'HARDWARE': ['fan', 'işlemci', 'cpu', 'ram', 'disk']
        }
        
        for _, keywords in problem_keywords.items():
            if any(keyword in problem_type.lower() for keyword in keywords):
                if any(keyword in solution_type.lower() for keyword in keywords):
                    return True
        return False

    def _normalize_text(self, text):
        """Metin normalizasyonu geliştirme"""
        text = str(text).lower().strip()
        
        # Eş anlamlı kelimeleri genişlet
        synonyms = {
            'outlook': ['mail', 'e-posta', 'eposta', 'email'],
            'tarayici': ['scanner', 'tarama', 'scan'],
            'yazici': ['printer', 'baski', 'çıktı', 'cikti'],
            'email': ['mail', 'e-posta', 'outlook'],
            'vpn': ['uzak bağlantı', 'remote'],
            'sap': ['erp', 'sistem']
        }
        
        # Eş anlamlıları ekle
        normalized = text
        for main_word, synonym_list in synonyms.items():
            if any(syn in text for syn in synonym_list):
                normalized = f"{normalized} {main_word}"
        
        # Türkçe karakterleri düzelt
        normalized = unidecode(normalized)
        
        # Gereksiz karakterleri kaldır
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        return normalized.strip()

    def _get_printer_solution(self, problem, model):
        """Yazıcı problemleri için özel çözümler"""
        problem = problem.lower()
        model = model.lower()
        
        printer_solutions = {
            'offline': [
                'Yazıcı ağ bağlantısı kontrol edildi',
                'IP adresi yeniden yapılandırıldı',
                'Yazıcı sürücüleri güncellendi'
            ],
            'renkli': [
                'Toner seviyeleri kontrol edildi',
                'Renkli yazdırma ayarları düzeltildi',
                'Renk kalibrasyonu yapıldı'
            ],
            'sikisma': [
                'Kağıt yolu temizlendi',
                'Kağıt besleme ünitesi kontrol edildi',
                'Yazıcı bakımı yapıldı'
            ],
            'cikti': [
                'Yazıcı sürücüleri güncellendi',
                'Yazdırma kuyruğu temizlendi',
                'Yazıcı ayarları sıfırlandı'
            ]
        }
        
        # Problem tipini belirle
        problem_type = None
        if any(word in problem for word in ['offline', 'çevrimdışı', 'bağlantı']):
            problem_type = 'offline'
        elif any(word in problem for word in ['renkli', 'renk', 'color']):
            problem_type = 'renkli'
        elif any(word in problem for word in ['sıkış', 'sikis', 'jam']):
            problem_type = 'sikisma'
        elif any(word in problem for word in ['çıktı', 'cikti', 'yazdır']):
            problem_type = 'cikti'
            
        if problem_type and problem_type in printer_solutions:
            return printer_solutions[problem_type]
        return None

    def _get_model_similarity(self, model1, model2):
        """İki modelin benzerliğini kontrol et"""
        if not model1 or not model2:
            return 0.0
            
        model1 = str(model1).lower().strip()
        model2 = str(model2).lower().strip()
        
        # Tam eşleşme
        if model1 == model2:
            return 1.0
            
        # Metin benzerliği hesapla
        vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(2, 3)
        )
        
        try:
            vectors = vectorizer.fit_transform([model1, model2])
            similarity = cosine_similarity(vectors)[0][1]
            return float(similarity)
        except:
            return 0.0

    def get_similar_tickets(self, problem, model, kategori, alt_kategori):
        """Benzer ticketları getir"""
        try:
            # Kategori ve alt kategoriye göre filtrele
            filtered_df = self.df[
                (self.df['kategori'] == kategori) & 
                (self.df['alt_kategori'] == alt_kategori)
            ]
            
            # Yeterli sonuç yoksa sadece kategori ile filtrele
            if len(filtered_df) < 5:
                filtered_df = self.df[self.df['kategori'] == kategori]
            
            # Benzerlik hesapla ve sonuçları döndür
            return self._find_similar_tickets(problem, filtered_df)
            
        except Exception as e:
            print(f"Hata: {str(e)}")
            return []

    def _find_similar_tickets(self, problem, df):
        """Benzer ticketları bul ve formatla"""
        try:
            results = []
            normalized_problem = self._normalize_text(problem)
            
            for _, row in df.iterrows():
                try:
                    other_problem = self._normalize_text(row['problem_description'])
                    similarity_score = self._calculate_similarity(normalized_problem, other_problem)
                    
                    if similarity_score > 0.1:  # Minimum benzerlik eşiği
                        results.append({
                            'similarity_score': round(float(similarity_score), 2),
                            'problem_description': str(row['problem_description']),
                            'solution_description': str(row['solution_description']),
                            'relevance': self._get_relevance_level(similarity_score)
                        })
                except Exception as e:
                    print(f"Satır işleme hatası: {str(e)}")
                    continue
            
            # Benzerlik skoruna göre sırala
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return results[:5]  # En benzer 5 sonucu döndür
            
        except Exception as e:
            print(f"Benzerlik hesaplama hatası: {str(e)}")
            return []

    def _get_relevance_level(self, score):
        """Benzerlik skoruna göre uyumluluk seviyesi belirle"""
        if score >= 0.7:
            return "Yüksek"
        elif score >= 0.3:
            return "Orta"
        else:
            return "Düşük"

    def get_total_tickets(self):
        """Toplam ticket sayısını getir"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM Tickets"))
                return result.scalar()
        except Exception as e:
            print(f"❌ Veritabanı hatası: {str(e)}")
            return 0

    def _calculate_similarity(self, text1, text2):
        """İki metin arasındaki benzerliği hesapla"""
        try:
            # Metinleri vektörlere dönüştür
            vector1 = self.vectorizer.transform([text1])
            vector2 = self.vectorizer.transform([text2])
            
            # Kosinüs benzerliğini hesapla
            similarity = cosine_similarity(vector1, vector2)[0][0]
            return float(similarity)
            
        except Exception as e:
            print(f"Benzerlik hesaplama hatası: {str(e)}")
            return 0.0
            