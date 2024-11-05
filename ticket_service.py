from flask import Flask, request, jsonify
from nlp_engine import NLPEngine
import traceback
from werkzeug.serving import run_simple

app = Flask(__name__)

# Global NLP nesnesi - Singleton pattern sayesinde tek instance
nlp = NLPEngine()
nlp.initialize()  # Sadece ilk çağrıda başlatılacak

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Service is running'})

@app.route('/api/ticket-details', methods=['POST'])
def get_ticket_details():
    try:
        data = request.get_json()
        problem = data.get('problem', '')
        
        if not problem:
            return jsonify({'error': 'Problem açıklaması boş olamaz'}), 400
            
        print(f"\n🔍 Aranan problem: {problem}")
        
        # NLP engine'den benzer ticketları al
        solutions = nlp.get_similar_tickets(problem)
        
        print(f"📊 Veritabanındaki toplam ticket sayısı: {nlp.get_total_tickets()}")
        print(f"🎯 Bulunan benzer çözüm sayısı: {len(solutions)}")
        
        if solutions:
            print("✅ Bulunan çözümler:")
            for s in solutions:
                print(f"- {s['Cozum_Aciklamasi'][:100]}...")
        else:
            print("⚠️ Benzer çözüm bulunamadı")
        
        return jsonify({'solutions': solutions})
        
    except Exception as e:
        print(f"❌ API hatası: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/learn', methods=['POST'])
def learn():
    try:
        data = request.get_json()
        problem = data.get('problem')
        solution = data.get('solution')
        ticket_details = data.get('ticket_details')
        
        if not all([problem, solution, ticket_details]):
            return jsonify({'error': 'Eksik veri'}), 400
            
        # Burada NLP öğrenme işlemleri yapılabilir
        # Örnek: Veritabanına kaydetme, model güncelleme vb.
        
        return jsonify({'message': 'Öğrenme başarılı'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        print("Servis başlatılıyor...")
        run_simple('0.0.0.0', 5000, app, use_reloader=False, use_debugger=False)
        
    except Exception as e:
        print(f"Servis başlatma hatası: {str(e)}")
        traceback.print_exc()