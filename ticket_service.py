from flask import Flask, request, jsonify
from nlp_engine import NLPEngine
import traceback
from werkzeug.serving import run_simple
from colorama import Fore, Style
import json

app = Flask(__name__)

# Global NLP nesnesi - Singleton pattern sayesinde tek instance
nlp = NLPEngine()
nlp.initialize()  # Sadece ilk çağrıda başlatılacak

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Service is running'})

def get_similar_tickets(problem, model, kategori, alt_kategori, musteri_id):
    """Benzer ticketları getir"""
    try:
        # Problemi normalize et
        normalized_problem = nlp._normalize_text(problem)
        
        # Kategori ve alt kategoriye göre filtrele
        filtered_df = nlp.df[
            (nlp.df['kategori'] == kategori) & 
            (nlp.df['alt_kategori'] == alt_kategori)
        ]
        
        # NLP motoruna gönder
        similar_tickets = nlp.get_similar_tickets(
            problem=normalized_problem,
            model=model,
            kategori=kategori,
            alt_kategori=alt_kategori,
            musteri_id=musteri_id
        )
        return similar_tickets
    except Exception as e:
        print(f"Hata: {str(e)}")
        return []

@app.route('/api/ticket-details', methods=['POST'])
def get_ticket_details():
    try:
        data = request.get_json()
        problem = data.get('problem')
        model = data.get('model')
        kategori = data.get('kategori')
        alt_kategori = data.get('alt_kategori')
        
        similar_tickets = get_similar_tickets(
            problem=problem,
            model=model,
            kategori=kategori,
            alt_kategori=alt_kategori,
            musteri_id=data.get('musteri_id')
        )
        
        return jsonify(similar_tickets)
        
    except Exception as e:
        print(f"Hata: {str(e)}")
        return jsonify([])

@app.route('/api/learn', methods=['POST'])
def learn():
    try:
        data = request.get_json()
        problem = data.get('problem')
        solution = data.get('solution')
        ticket_details = data.get('ticket_details')
        model = data.get('model')
        musteri_id = data.get('musteri_id')
        
        if not all([problem, solution, ticket_details, model, musteri_id]):
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