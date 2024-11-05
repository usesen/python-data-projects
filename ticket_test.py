from NLP_demo import get_similar_tickets
import pandas as pd
pd.set_option('display.max_columns', None)  # Tüm sütunları göster

def test_problem_cozumu(problem_metni):
    print(f"\nTest Problemi: {problem_metni}")
    print("=" * 70)
    
    # Benzer ticketları bul
    similar_tickets = get_similar_tickets(problem_metni)
    
    # Sonuçları göster
    for _, ticket in similar_tickets.iterrows():
        print("\n--- Ticket Detayları ---")
        print(f"Ticket ID: {ticket['Ticket_ID']}")
        print(f"Benzerlik Skoru: {ticket['Benzerlik_Skoru']:.2%}")
        print(f"Kategori: {ticket['Kategori']} - {ticket['Alt_Kategori']}")
        print(f"Tahmini Kategori: {ticket['Tahmini_Kategori']} - {ticket['Tahmini_Alt_Kategori']}")
        print(f"Problem: {ticket['Problem_Aciklamasi']}")
        print(f"Çözüm: {ticket['Cozum_Aciklamasi']}")
        print(f"Önerilen Çözüm: {ticket['Onerilen_Cozum']}")
        
        if pd.notna(ticket['Yapilan_Islem']):
            print(f"Yapılan İşlem: {ticket['Yapilan_Islem']}")
        
        if pd.notna(ticket['Kullanilan_Arac']):
            print(f"Kullanılan Araç: {ticket['Kullanilan_Arac']}")
        
        print(f"Teknisyen: {ticket['Teknisyen']} ({ticket['Teknisyen_Seviye']})")
        print(f"Müşteri Memnuniyeti: {ticket['Musteri_Memnuniyeti']:.1f}/5.0")
        print("-" * 50)

if __name__ == "__main__":
    # Test senaryoları
    test_problemleri = [
        "Excel dosyası açılmıyor, sürekli kilitleniyor",
        "Bilgisayar çok yavaş açılıyor ve fan sesi çok yüksek",
        "Yazıcıdan çıktı alamıyorum, sürekli kağıt sıkışıyor",
        "SAP'a bağlanamıyorum, timeout hatası alıyorum",
        "VPN bağlantısı kurulamıyor, sürekli kopuyor",
        "Outlook sürekli yanıt vermiyor hatası veriyor",
        "İnternet çok yavaş, sayfalara giremiyorum"
    ]
    
    for problem in test_problemleri:
        test_problem_cozumu(problem)
        print("\n" + "="*70 + "\n") 