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
from routes.analytics_routes import analytics_bp
from routes.linkedin import linkedin_bp
from routes.cv_parser import cv_parser_bp

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Criar aplicação Flask
app = Flask(__name__)

# Configuração CORS explícita para permitir domínios específicos
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "*",  # Allow all for development
            "https://share2inspire.pt",
            "https://www.share2inspire.pt",
            "https://share2inspire-cv-analyser.vercel.app",
            "https://cv-compass.vercel.app",
            "https://cv-compass-*.vercel.app",  # Preview deployments
        ],
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

# /api/analytics/...
app.register_blueprint(analytics_bp, url_prefix='/api/analytics')

# /api/linkedin/...
app.register_blueprint(linkedin_bp, url_prefix='/api/linkedin')

# /api/cv/...
app.register_blueprint(cv_parser_bp, url_prefix='/api/cv')


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
    from gunicorn.app.base import BaseApplication

    class StandaloneApplication(BaseApplication):
        def __init__(self, app, options=None):
            self.application = app
            self.options = options or {}
            super().__init__()

        def load_config(self):
            config = {key: value for key, value in self.options.items() if key in self.cfg.settings and value is not None}
            for key, value in config.items():
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    options = {
        'bind': '%s:%s' % ('0.0.0.0', os.environ.get('PORT', '8080')),
        'workers': 1, # Pode ser ajustado, mas 1 é bom para depuração
        'timeout': 120, # Aumentar o timeout para 120 segundos
        'worker_class': 'sync', # Usar worker síncrono
    }
    StandaloneApplication(app, options).run()
