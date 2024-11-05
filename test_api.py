import requests
import json
from datetime import datetime

def test_similarity(problem):
    print(f"\nTest Problemi: {problem}")
    print("="*50)
    
    try:
        response = requests.post(
            "http://localhost:5000/api/similar-tickets",
            json={"problem": problem}
        )
        
        result = response.json()
        if 'tickets' in result:
            for ticket in result['tickets'][:3]:  # İlk 3 benzer ticket
                print(f"\nBenzerlik Skoru: {ticket['similarity']}")
                print(f"Kategori: {ticket['category']}")
                print(f"Problem: {ticket['problem']}")
                print(f"Çözüm: {ticket['solution']}")
                print("-" * 30)
        else:
            print(f"Hata: {result}")
            
    except Exception as e:
        print(f"Hata: {str(e)}")

print(f"\nTest başlangıç zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Test problemleri - güncellenmiş liste
test_cases = [
    "Excel dosyası açılmıyor, sürekli kilitleniyor",
    "Bilgisayar çok yavaş açılıyor ve fan sesi çok yüksek",
    "Yazıcıdan çıktı alamıyorum, sürekli kağıt sıkışıyor",
    "SAP'a bağlanamıyorum, timeout hatası alıyorum",
    "VPN bağlantısı kurulamıyor, sürekli kopuyor",
    "Outlook sürekli yanıt vermiyor hatası veriyor"
]

for problem in test_cases:
    test_similarity(problem)
