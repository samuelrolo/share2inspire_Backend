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
CORS(app)

# Registar Blueprints
# /api/payment/...
app.register_blueprint(payment_bp, url_prefix='/api/payment')
# /api/booking/...
app.register_blueprint(booking_bp, url_prefix='/api/booking')
# /api/services/...
app.register_blueprint(services_bp, url_prefix='/api/services')


# === ROTAS DE SAÚDE ===

@app.route('/')
def health_check():
    return jsonify({
        "message": "Share2Inspire Backend - Modular",
        "status": "online",
        "timestamp": datetime.now().isoformat()
    })

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
