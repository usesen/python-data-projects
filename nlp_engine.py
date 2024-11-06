import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pyodbc
import traceback
from unidecode import unidecode
import re
import random

class NLPEngine:
    def __init__(self):
        self.conn = None
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
        try:
            self.conn = pyodbc.connect(
                'DRIVER={SQL Server};'
                'SERVER=DESKTOP-6QR83E3\\UGURMSSQL;'
                'DATABASE=FSM_Tickets;'
                'UID=usesen;'
                'PWD=usesen'
            )
            print("✅ Veritabanı bağlantısı kuruldu")
        except Exception as e:
            print(f"❌ Veritabanı bağlantı hatası: {str(e)}")
            raise
        
    def _load_data(self):
        """Ticket verilerini yükle"""
        query = """
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
                AND t.Cozum_Aciklamasi != 'Standart prosedür uygulandı'
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
        """
        
        cursor = self.conn.cursor()
        result = cursor.execute(query)
        
        # Sütun isimlerini al
        columns = [column[0] for column in cursor.description]
        
        # Verileri DataFrame'e dönüştür
        self.df = pd.DataFrame.from_records(result.fetchall(), columns=columns)
        
        print("\n=== Veri Yükleme Kontrolü ===")
        print(f"Toplam benzersiz kayıt: {len(self.df)}")
        print("Örnek problem-çözüm çiftleri:")
        sample_data = self.df.sample(n=3) if len(self.df) > 3 else self.df
        for _, row in sample_data.iterrows():
            print(f"\nProblem: {row['problem_description']}")
            print(f"Çözüm: {row['solution_description']}")
            
    def get_total_tickets(self):
        """Toplam ticket sayısını getir"""
        try:
            cursor = self.conn.cursor()
            result = cursor.execute("SELECT COUNT(*) FROM Tickets")
            return result.fetchone()[0]
        except Exception as e:
            print(f"❌ Veritabanı hatası: {str(e)}")
            return 0
            
    def _insert_ticket(self, problem, model, kategori, alt_kategori, musteri_id):
        """Yeni ticket'ı veritabanına ekle"""
        try:
            print("\n📝 Ticket kayıt işlemi başladı")
            cursor = self.conn.cursor()
            
            # Son ticket ID'yi al
            cursor.execute("SELECT MAX(CAST(SUBSTRING(Ticket_ID, 4, LEN(Ticket_ID)) AS INT)) FROM Tickets")
            last_id = cursor.fetchone()[0]
            new_id = last_id + 1 if last_id else 1
            ticket_id = f'TIC{new_id:06d}'
            
            print(f"📋 Kaydedilecek ticket bilgileri:")
            print(f"Ticket ID: {ticket_id}")
            print(f"Problem: {problem}")
            print(f"Model: {model}")
            print(f"Kategori: {kategori}")
            print(f"Alt Kategori: {alt_kategori}")
            print(f"Müşteri ID: {musteri_id}")
            
            # Insert query - solution alanı yok
            query = """
            INSERT INTO Tickets (
                Ticket_ID, Problem_Aciklamasi, Model, 
                Kategori, Alt_Kategori, Musteri_ID
            ) VALUES (?, ?, ?, ?, ?, ?)
            """
            
            params = (ticket_id, problem, model, kategori, alt_kategori, musteri_id)
            
            cursor.execute(query, params)
            self.conn.commit()
            print(f"✅ Ticket başarıyla kaydedildi: {ticket_id}")
            
        except Exception as e:
            print(f"❌ Ticket kayıt hatası: {str(e)}")
            self.conn.rollback()
            raise
            
    def get_similar_tickets(self, problem, model, kategori, alt_kategori, musteri_id):
        """Benzer ticketları getir"""
        try:
            print("\n🔍 Benzer ticket arama başladı")
            print(f"Aranan problem: {problem}")
            print(f"Kategori: {kategori}")
            print(f"Alt Kategori: {alt_kategori}")
            print(f"Müşteri ID: {musteri_id}")
            
            # Problemi normalize et
            normalized_problem = self._normalize_text(problem)
            print(f"Normalize edilmiş problem: {normalized_problem}")
            
            # Veritabanında bu kategoride kayıt var mı?
            filtered_df = self.df[
                (self.df['kategori'] == kategori) & 
                (self.df['alt_kategori'] == alt_kategori)
            ]
            print(f"Bu kategori için kayıt sayısı: {len(filtered_df)}")
            
            results = []
            print("\n📊 Benzerlik karşılaştırmaları:")
            for _, row in filtered_df.iterrows():
                try:
                    other_problem = self._normalize_text(row['problem_description'])
                    similarity_score = self._calculate_similarity(normalized_problem, other_problem)
                    print(f"\nKarşılaştırılan problem: {row['problem_description']}")
                    print(f"Benzerlik skoru: {similarity_score:.2f}")
                    print(f"Çözüm var mı?: {'Evet' if row['solution_description'] and str(row['solution_description']).strip() else 'Hayır'}")
                    
                    if similarity_score > 0.1 and row['solution_description'] and str(row['solution_description']).strip():
                        result = {
                            'similarity_score': round(float(similarity_score), 2),
                            'problem_description': str(row['problem_description']),
                            'solution_description': str(row['solution_description']),
                            'relevance': self._get_relevance_level(similarity_score)
                        }
                        results.append(result)
                        print("✅ Bu sonuç listeye eklendi")
                    else:
                        print("❌ Bu sonuç listeye eklenmedi (Düşük benzerlik veya çözüm yok)")
                except Exception as e:
                    print(f"❌ Satır karşılaştırma hatası: {str(e)}")
                    continue
            
            # Results içeriğini göster
            print("\n📋 Results listesi içeriği:")
            if results:
                for i, result in enumerate(results, 1):
                    print(f"\nSonuç #{i}:")
                    print(f"Benzerlik: {result['similarity_score']}")
                    print(f"Problem: {result['problem_description']}")
                    print(f"Çözüm: {result['solution_description']}")
                    print(f"Uyumluluk: {result['relevance']}")
            else:
                print("Liste boş!")
            
            # Benzerlik skoruna göre sırala
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Çözüm bulunamadıysa yeni ticket oluştur
            if not results:
                print(f"\n⚠️ Benzer çözüm bulunamadı. Yeni ticket oluşturuluyor...")
                print(f"📝 Yeni ticket bilgileri:")
                print(f"Problem: {problem}")
                print(f"Model: {model}")
                print(f"Kategori: {kategori}")
                print(f"Alt Kategori: {alt_kategori}")
                print(f"Müşteri ID: {musteri_id}")
                
                self._insert_ticket(
                    problem=problem,
                    model=model,
                    kategori=kategori,
                    alt_kategori=alt_kategori,
                    musteri_id=musteri_id
                )
                print("✅ Yeni ticket kaydedildi")
                
                print("\n🔄 Veriler yeniden yükleniyor...")
                self.initialize()
                print("✅ Veriler güncellendi")
                
                return []
                
            print(f"\n✅ {len(results)} benzer çözüm bulundu")
            return results[:5]
                
        except Exception as e:
            print(f"❌ Genel hata: {str(e)}")
            return []

    def _is_valid_category(self, kategori, alt_kategori):
        """Kategori ve alt kategori kombinasyonunun geçerli olup olmadığını kontrol et"""
        valid_combinations = {
            'Ağ': ['İnternet', 'VPN', 'Ağ Erişimi'],
            'Donanım': ['PC Arıza', 'Yazıcı Arıza'],
            'Yazılım': ['Office', 'ERP']
        }
        
        return kategori in valid_combinations and alt_kategori in valid_combinations[kategori]

    def _normalize_text(self, text):
        """Metin normalizasyonu"""
        try:
            # None veya boş string kontrolü
            if not text:
                return ""
                
            # String'e çevir ve küçük harfe dönüştür
            text = str(text).lower().strip()
            
            # Türkçe karakterleri dönüştür
            text = unidecode(text)
            
            # Gereksiz karakterleri kaldır
            text = re.sub(r'[^\w\s]', ' ', text)
            
            # Fazla boşlukları temizle
            text = ' '.join(text.split())
            
            return text
            
        except Exception as e:
            print(f"Normalizasyon hatası: {str(e)}")
            return ""
            
    def _calculate_similarity(self, text1, text2):
        """İki metin arasındaki benzerliği hesapla"""
        try:
            # Vectorizer kontrolü
            if self.vectorizer is None:
                print("⚠️ Model eğitilmemiş, yeniden eğitiliyor...")
                self._train_model()
                if self.vectorizer is None:
                    return 0.0
                
            # Metinleri vektörlere dönüştür
            vector1 = self.vectorizer.transform([text1])
            vector2 = self.vectorizer.transform([text2])
            
            # Kosinüs benzerliğini hesapla
            similarity = cosine_similarity(vector1, vector2)[0][0]
            
            return float(similarity)
            
        except Exception as e:
            print(f"Benzerlik hesaplama hatası: {str(e)}")
            return 0.0
            
    def _get_relevance_level(self, score):
        """Benzerlik skoruna göre uyumluluk seviyesi belirle"""
        if score >= 0.7:
            return "Yüksek"
        elif score >= 0.3:
            return "Orta"
        else:
            return "Düşük"
            
    def _setup_categories(self):
        """Kategorileri ayarla"""
        self.categories = {
            'donanim': {'keywords': {'bilgisayar', 'ekran', 'yazıcı', 'fare', 'klavye', 'monitör', 'printer'}},
            'yazilim': {'keywords': {'windows', 'office', 'excel', 'word', 'outlook', 'uygulama'}},
            'ag': {'keywords': {'internet', 'wifi', 'bağlantı', 'ağ', 'network', 'vpn'}}
        }

    def _train_model(self):
        """TF-IDF modelini eğit"""
        try:
            if self.df is not None and not self.df.empty:
                # Vectorizer'ı başlat ve eğit
                self.vectorizer = TfidfVectorizer(
                    analyzer='word',
                    lowercase=True,
                    max_features=5000
                )
                # Problem açıklamalarıyla eğit
                self.vectorizer.fit(self.df['problem_description'].fillna(''))
                print("✅ Model eğitimi tamamlandı")
            else:
                print("⚠️ Eğitim verisi bulunamadı")
                
        except Exception as e:
            print(f"❌ Model eğitim hatası: {str(e)}")
            self.vectorizer = None
            