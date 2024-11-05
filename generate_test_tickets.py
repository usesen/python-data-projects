import random
import requests
from datetime import datetime, timedelta

# Test verisi oluştur
problems = [
    "Yazıcı çıktı vermiyor",
    "Network bağlantısı kopuyor",
    "Excel dosyası açılmıyor",
    "Bilgisayar çok yavaş",
    "VPN bağlantısı kurulamıyor"
]

categories = [
    ("Donanım", "Yazıcı Arıza"),
    ("Ağ", "Network"),
    ("Yazılım", "Office"),
    ("Donanım", "PC Arıza"),
    ("Ağ", "VPN")
]

technicians = [
    ("Teknisyen_1", "Junior"),
    ("Teknisyen_2", "Mid-Level"),
    ("Teknisyen_3", "Senior")
]

tools = ["TeamViewer", "Remote Desktop", "Yerinde Müdahale", "VNC"]

print("Test ticket'ları oluşturuluyor...")

# Son 24 saat için rastgele ticket'lar oluştur
for i in range(10):  # 10 yeni ticket
    problem = random.choice(problems)
    category = random.choice(categories)
    technician = random.choice(technicians)
    tool = random.choice(tools)
    
    # API'yi çağır
    data = {
        "problem": problem,
        "category": category[0],
        "sub_category": category[1],
        "technician": technician[0],
        "technician_level": technician[1],
        "tool": tool
    }
    
    try:
        print(f"\nTicket {i+1}/10 ekleniyor...")
        print(f"Problem: {problem}")
        print(f"Kategori: {category[0]} - {category[1]}")
        
        response = requests.post("http://localhost:5000/api/add-ticket", json=data)
        print(f"Sonuç: {response.json()}")
    except Exception as e:
        print(f"Hata: {str(e)}")

print("\nİşlem tamamlandı!")