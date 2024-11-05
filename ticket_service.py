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
            
        solutions = nlp.get_similar_tickets(problem)
        return jsonify({'solutions': solutions})
        
    except Exception as e:
        print(f"API hatası: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        print("Servis başlatılıyor...")
        run_simple('0.0.0.0', 5000, app, use_reloader=False, use_debugger=False)
        
    except Exception as e:
        print(f"Servis başlatma hatası: {str(e)}")
        traceback.print_exc()