import requests
import json
import time
import random
from colorama import init, Fore, Style
from nlp_engine import NLPEngine

# Renk desteği için
init()

# API URL'leri
BASE_URL = 'http://127.0.0.1:5000'
API_URL = f'{BASE_URL}/api/ticket-details'
LEARN_URL = f'{BASE_URL}/api/learn'

# Dinamik ticket oluşturmak için veri setleri
DEVICES = ['Yazıcı', 'Bilgisayar', 'Monitör', 'Laptop', 'VPN', 'Teams', 'Outlook', 'Excel', 'Word', 'SAP']
PROBLEMS = ['çalışmıyor', 'açılmıyor', 'hata veriyor', 'yavaş', 'kilitleniyor', 'yanıt vermiyor', 'bağlanmıyor']
SYMPTOMS = ['mavi ekran', 'siyah ekran', 'sürekli reset atıyor', 'fan sesi geliyor', 'kağıt sıkışıyor', 
           'internet yok', 'dosya açılmıyor', 'e-posta göndermiyor', 'bellek yetersiz']
LOCATIONS = ['3. kat', '4. kat', 'toplantı odası', 'ofis', 'uzaktan çalışma']

# Yeni veri setleri ekleyelim
REGIONS = ['İstanbul', 'Ankara', 'İzmir', 'Bursa', 'Antalya']
PRIORITIES = ['Düşük', 'Orta', 'Yüksek', 'Kritik']
CATEGORIES = ['Donanım', 'Yazılım', 'Network', 'Güvenlik', 'Uygulama']
SUBCATEGORIES = ['Kurulum', 'Arıza', 'Güncelleme', 'Erişim', 'Performans']
TECHNICIANS = ['Ahmet Yılmaz', 'Mehmet Demir', 'Ayşe Kaya', 'Ali Öz', 'Fatma Şahin']
TECH_LEVELS = ['Junior', 'Mid-Level', 'Senior', 'Expert']

class NLPTester:
    def __init__(self):
        self.ticket_counter = 1000
        self.nlp = NLPEngine()
        
        # API bağlantısı için
        self.api_url = API_URL
        self.session = requests.Session()

    def test_ticket(self, problem):
        """Test bir ticket oluştur ve sonuçları göster"""
        print("\n=== Yeni Test Problemi ===\n")
        print(f"📝 Problem: {problem}\n")
        print("🔍 Benzer ticket'lar aranıyor...\n")

        try:
            # API üzerinden benzer ticketları al
            response = self.session.post(
                self.api_url,
                json={'problem': problem}
            )
            
            if response.status_code == 200:
                data = response.json()
                if solutions := data.get('solutions', []):
                    print("📋 Benzer Ticket Çözüm Önerileri:\n")
                    for i, solution in enumerate(solutions, 1):
                        print(f"💡 Çözüm #{i}")
                        print(f"✅ Çözüm: {solution['Cozum_Aciklamasi']}")
                        print(f"📊 Benzerlik: {solution.get('Benzerlik_Skoru', 0)}%\n")
                else:
                    print("⚠️ Benzer çözüm bulunamadı\n")
            else:
                print(f"❌ API Hatası: {response.status_code}\n")
                
        except Exception as e:
            print(f"❌ Hata: {str(e)}\n")

        print("=" * 50)

    def run_tests(self):
        """Tüm test senaryolarını çalıştır"""
        test_cases = [
            "Bilgisayar çok yavaş açılıyor ve fan sesi yüksek",
            "Yazıcı kağıt sıkıştırıyor ve çıktı alamıyorum",
            "Outlook açılmıyor ve e-posta gönderemiyor",
            "SAP sistemine giriş yapılamıyor, ekran donuyor",
            "VPN bağlantısı sürekli kopuyor",
            "İnternet çok yavaş, sayfalara giremiyorum"
        ]

        for test_case in test_cases:
            self.test_ticket(test_case)

def check_service():
    """Servis durumunu kontrol et"""
    max_retries = 3
    retry_delay = 2
    
    for i in range(max_retries):
        try:
            response = requests.get(f'{BASE_URL}/')
            if response.status_code == 200:
                print(f"{Fore.GREEN}✅ Servis çalışıyor{Style.RESET_ALL}")
                return True
                
        except requests.exceptions.ConnectionError:
            if i < max_retries - 1:
                print(f"Servis kontrol ediliyor... ({i+1}/{max_retries})")
                time.sleep(retry_delay)
            continue
            
    print(f"{Fore.RED}❌ UYARI: Servis çalışmıyor!")
    print("   Lütfen önce 'python ticket_service.py' çalıştırın{Style.RESET_ALL}")
    return False

if __name__ == '__main__':
    tester = NLPTester()
    
    print(f"{Fore.CYAN}NLP Öğrenme Testi Başlıyor...{Style.RESET_ALL}")
    print("Servis kontrolü yapılıyor...")
    
    if check_service():
        tester.run_tests()