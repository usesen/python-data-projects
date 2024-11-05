import requests
import json
import time

# API URL'leri
BASE_URL = 'http://127.0.0.1:5000'  # localhost yerine 127.0.0.1 kullan
API_URL = f'{BASE_URL}/api/ticket-details'

def check_service():
    """Servis durumunu kontrol et"""
    max_retries = 3
    retry_delay = 2  # saniye
    
    for i in range(max_retries):
        try:
            response = requests.get(f'{BASE_URL}/')
            if response.status_code == 200:
                print("✅ Servis çalışıyor")
                return True
                
        except requests.exceptions.ConnectionError:
            if i < max_retries - 1:  # Son deneme değilse
                print(f"Servis kontrol ediliyor... ({i+1}/{max_retries})")
                time.sleep(retry_delay)
            continue
            
    print("❌ UYARI: Servis çalışmıyor!")
    print("   Lütfen önce 'python ticket_service.py' çalıştırın")
    return False

def test_ticket(problem):
    """Ticket testi yap"""
    print(f"\n🔍 Yeni Ticket: {problem}")
    print("="*50)
    
    try:
        response = requests.post(
            API_URL,
            json={'problem': problem},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            solutions = data.get('solutions', [])
            
            if not solutions:
                print("❌ Benzer ticket bulunamadı!")
                return
                
            for i, solution in enumerate(solutions, 1):
                print(f"\n💡 Benzer Ticket #{i}")
                print("-"*22)
                print(f"📊 Benzerlik Oranı: {solution.get('Benzerlik_Skoru', 0):.2f}%")
                print(f"❗ Problem: {solution.get('Problem_Aciklamasi', '')}")
                print(f"✅ Çözüm: {solution.get('Cozum_Aciklamasi', '')}")
                print(f"📝 Yapılan İşlemler:")
                print(solution.get('Yapilan_Islemler', ''))
                print(f"👨‍💻 Teknisyen: {solution.get('Teknisyen', '')}")
        else:
            print(f"❌ Hata: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Bağlantı hatası: Servis çalışmıyor olabilir")
    except Exception as e:
        print(f"❌ Hata: {str(e)}")

# Test senaryoları
test_cases = [
    "Yazıcı sürekli kağıt sıkıştırıyor",
    "VPN bağlantısı kopuyor ve tekrar bağlanmıyor",
    "Excel dosyası açılmıyor, hata veriyor"
]

if __name__ == '__main__':
    print("NLP Test Başlıyor...")
    print("Servis kontrolü yapılıyor...")
    
    if check_service():  # Servis çalışıyorsa testleri başlat
        for test in test_cases:
            test_ticket(test)