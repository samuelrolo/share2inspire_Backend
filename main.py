"""
Share2Inspire Backend - Modular Version
"""

import os
import logging
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from routes.payment import payment_bp
from routes.booking import booking_bp
from routes.services import services_bp

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Criar aplicação Flask
app = Flask(__name__)

# Configuração CORS explícita para permitir todas as origens
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "supports_credentials": False
    }
})

# Registar Blueprints
# /api/payment/...
app.register_blueprint(payment_bp, url_prefix='/api/payment')
# /api/booking/...
app.register_blueprint(booking_bp, url_prefix='/api/booking')
# /api/services/...
# /api/services/...
app.register_blueprint(services_bp, url_prefix='/api/services')

# /api/feedback/...
from routes.feedback import feedback_bp
if feedback_bp:
    app.register_blueprint(feedback_bp, url_prefix='/api/feedback')


# === ROTAS DE SAÚDE ===

@app.route('/')
def health_check():
    return jsonify({
        "message": "Share2Inspire Backend - Modular",
        "status": "online",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/debug/models', methods=['GET'])
def list_models():
    try:
        from utils.secrets import get_secret
        import google.generativeai as genai
        
        api_key = get_secret('GEMINI_API_KEY')
        if not api_key:
            return jsonify({'error': 'No API Key'}), 500
            
        genai.configure(api_key=api_key)
        
        models = []
        for m in genai.list_models():
            models.append({
                'name': m.name,
                'supported_generation_methods': m.supported_generation_methods
            })
            
        return jsonify({'models': models})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def api_health():
    return jsonify({
        "service": "share2inspire-backend",
        "status": "healthy",
        "version": "modular-1.0.0",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
