#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação principal do backend Share2Inspire
Versão CORRIGIDA com importações da pasta routes
"""

import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS 
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Criar aplicação Flask
app = Flask(__name__)

# Configuração CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "supports_credentials": True
    }
})

# Configurar chave secreta
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24).hex())

# Middleware global para garantir cabeçalhos CORS
@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Função para tratar preflight requests
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path=''):
    return jsonify({"success": True}), 200

# Rota principal
@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Share2Inspire Backend",
        "version": "1.0.0"
    })

# === IMPORTAR E REGISTRAR BLUEPRINTS ===

# Importar blueprints da pasta routes
try:
    from routes.fedback import fedback_bp
    app.register_blueprint(fedback_bp, url_prefix='/api')
    logger.info("Blueprint de feedback registrado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de feedback: {e}")

try:
    from routes.payment import payment_bp
    app.register_blueprint(payment_bp, url_prefix='/api')
    logger.info("Blueprint de payment registrado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de payment: {e}")

try:
    from routes.ifthenpay import ifthenpay_bp
    app.register_blueprint(ifthenpay_bp, url_prefix='/api')
    logger.info("Blueprint de ifthenpay registrado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de ifthenpay: {e}")

try:
    from routes.email_service import email_bp
    app.register_blueprint(email_bp, url_prefix='/api')
    logger.info("Blueprint de email registrado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de email: {e}")

try:
    from routes.booking import booking_bp
    app.register_blueprint(booking_bp, url_prefix='/api')
    logger.info("Blueprint de booking registrado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de booking: {e}")

try:
    from routes.user import user_bp
    app.register_blueprint(user_bp, url_prefix='/api')
    logger.info("Blueprint de user registrado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de user: {e}")

# === ROTAS ADICIONAIS ===

@app.route('/health')
def health_check():
    """Verificação de saúde do sistema"""
    return jsonify({
        "status": "healthy",
        "timestamp": "2025-07-07T12:00:00Z",
        "services": {
            "brevo": bool(os.getenv('BREVO_API_KEY')),
            "ifthenpay_multibanco": bool(os.getenv('IFTHENPAY_MULTIBANCO_KEY')),
            "ifthenpay_mbway": bool(os.getenv('IFTHENPAY_MBWAY_KEY')),
            "ifthenpay_payshop": bool(os.getenv('IFTHENPAY_PAYSHOP_KEY'))
        }
    })

# === TRATAMENTO DE ERROS ===

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Endpoint não encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Erro interno do servidor"}), 500

# === INICIALIZAÇÃO ===

if __name__ == '__main__':
    # Verificar variáveis de ambiente
    logger.info("=== VERIFICAÇÃO DE VARIÁVEIS DE AMBIENTE ===")
    
    env_vars = [
        'BREVO_API_KEY', 'BREVO_SENDER_EMAIL', 'BREVO_SENDER_NAME',
        'IFTHENPAY_MULTIBANCO_KEY', 'IFTHENPAY_MBWAY_KEY', 'IFTHENPAY_PAYSHOP_KEY'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "****"
            logger.info(f"{var}: DEFINIDA ({masked})")
        else:
            logger.warning(f"{var}: NÃO DEFINIDA")
    
    logger.info("=== BACKEND SHARE2INSPIRE INICIADO ===")
    
    # Executar aplicação
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

