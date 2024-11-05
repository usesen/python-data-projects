import requests
import json

def test_ticket_details(problem):
    """Teknisyen için ticket detaylarını test et"""
    print(f"\n🎫 Ticket Detayları")
    print("=" * 50)
    print(f"Problem: {problem}")
    print("-" * 50)
    
    try:
        response = requests.post(
            "http://localhost:5000/api/ticket-details",
            json={"problem": problem}
        )
        
        result = response.json()
        details = result['ticket_details']
        
        print("\n📋 Önerilen Çözümler:")
        for idx, solution in enumerate(details['suggested_solutions'], 1):
            print(f"""
Çözüm #{idx} (Benzerlik: {solution['similarity']})
------------------------------------------
🏷️ Kategori: {solution['category']} - {solution['sub_category']}
❗ Problem: {solution['problem']}
✅ Çözüm: {solution['solution']}

📝 Adımlar:
{chr(10).join(f'  {i+1}. {step}' for i, step in enumerate(solution['steps']))}

🛠️ Kullanılan Araçlar: {solution['tools']}
👨‍💻 Teknisyen: {solution['technician']['name']} ({solution['technician']['level']})
⭐ Müşteri Memnuniyeti: {solution['satisfaction']}
⏱️ Tahmini Süre: {solution['resolution_time']}
            """)
        
        print(f"\n🛠️ Gerekli Araçlar: {', '.join(details['tools_needed'])}")
        print(f"⏱️ Tahmini Çözüm Süresi: {details['estimated_time']}")
        print(f"📌 Öncelik: {details['priority']}")
        print(f"📝 Notlar: {details['notes']}")
        
    except Exception as e:
        print(f"❌ Hata: {str(e)}")

# Test et
test_ticket_details("Outlook sürekli yanıt vermiyor ve çok yavaş") 