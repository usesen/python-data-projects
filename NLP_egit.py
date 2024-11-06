from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from sqlalchemy import create_engine, text
import re

class TicketMatcher:
    def __init__(self):
        self.df = None
        self.vectorizer = None
        self.engine = create_engine('mssql+pyodbc://usesen:usesen@DESKTOP-6QR83E3\\UGURMSSQL/FSM_Tickets?driver=SQL+Server')
        
    def load_data(self):
        """SQL'den ticket verilerini yükle"""
        query = text("""
            SELECT Problem_Aciklamasi, Cozum_Aciklamasi
            FROM Tickets
        """)
        
        self.df = pd.read_sql(query, self.engine)
        print(f"✓ {len(self.df)} ticket yüklendi")
        
    def train_model(self):
        """TF-IDF modelini eğit"""
        self.df['processed_problem'] = self.df['Problem_Aciklamasi'].str.lower()
        
        self.vectorizer = TfidfVectorizer(max_features=5000)
        self.vectorizer.fit(self.df['processed_problem'])
        print("✓ Model eğitildi")
        
    def find_similar(self, problem, top_n=3):
        """Benzer ticketları bul"""
        problem = problem.lower()
        problem_vec = self.vectorizer.transform([problem])
        
        similarities = (problem_vec * self.vectorizer.transform(
            self.df['processed_problem']
        ).T).toarray()[0]
        
        top_matches = similarities.argsort()[-top_n:][::-1]
        
        print(f"\nProblem: {problem}")
        print("\nBenzer Çözümler:")
        for idx in top_matches:
            print(f"- {self.df.iloc[idx]['Cozum_Aciklamasi']}")
            print(f"  Benzerlik: {similarities[idx]:.2%}\n")

# Kullanım
matcher = TicketMatcher()
matcher.load_data()
matcher.train_model()

# Test et
test_problem = "Outlook açılmıyor"
matcher.find_similar(test_problem)