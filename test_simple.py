from veri_olustur import (
    problem_detaylari, 
    model_listesi, 
    musteri_idleri,
    kategoriler,
    cozum_detaylari
)
import random
import requests

def generate_random_ticket():
    # Kategori ve alt kategori seç
    kategori = random.choice(list(kategoriler.keys()))
    alt_kategori = random.choice(kategoriler[kategori])
    
    # Alt kategoriye göre problem seç
    if alt_kategori in problem_detaylari:
        problem = random.choice(problem_detaylari[alt_kategori])
    else:
        return generate_random_ticket()
    
    # Probleme uygun model seç
    if kategori == 'Yazılım':
        model = f'Software v{random.randint(1,5)}.{random.randint(0,9)}'
    elif kategori == 'Ağ':
        model = f'Network Device v{random.randint(1,3)}'
    else:
        model = random.choice(['HP EliteBook 840', 'Dell Latitude 5520', 'HP ProBook 450'])
    
    return {
        "problem": problem,
        "model": model,
        "musteri_id": random.randint(1001, 1999),
        "kategori": kategori,
        "alt_kategori": alt_kategori
    }

def test_multiple_random_tickets():
    test_count = 5
    print(f"\n🔍 {test_count} adet rastgele test senaryosu oluşturuluyor...\n")
    
    for i in range(test_count):
        ticket = generate_random_ticket()
        print(f"\n=== Test #{i+1} ===")
        print(f"📝 Problem: {ticket['problem']}")
        print(f"🔧 Model: {ticket['model']}")
        print(f"👤 Müşteri ID: {ticket['musteri_id']}")
        print(f"📂 Kategori: {ticket['kategori']}")
        print(f"📁 Alt Kategori: {ticket['alt_kategori']}\n")
        
        response = requests.post(
            "http://localhost:5000/api/ticket-details",
            json=ticket
        )
        
        if response.status_code == 200:
            solutions = response.json()
            if solutions:
                print("✅ API Yanıtı:")
                for solution in solutions:
                    print(f"\n🎯 Benzerlik: {solution['similarity_score']}")
                    print(f"📝 Problem: {solution['problem_description']}")
                    print(f"🔧 Çözüm: {solution['solution_description']}")
                    print(f"📊 Uyumluluk: {solution['relevance']}")
                    print("-" * 50)
            else:
                print("⚠️ Benzer çözüm bulunamadı")
        else:
            print(f"❌ Hata: {response.status_code}")
            print(f"Hata Detayı: {response.text}")
        
        if i < test_count - 1:
            print("\nDevam etmek için Enter'a basın...")
            input()

if __name__ == "__main__":
    test_multiple_random_tickets()