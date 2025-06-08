#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Aplicação principal do backend Share2Inspire
Versão final com configuração CORS corrigida para aceitar share2inspire.pt
"""

import os
import logging
from flask import Flask, Blueprint, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Criar aplicação Flask
app = Flask(__name__)

# Configuração CORS corrigida para aceitar share2inspire.pt
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://share2inspire.pt",           # Domínio de produção
            "http://share2inspire.pt",            # Versão HTTP do domínio
            "https://www.share2inspire.pt",       # Versão www do domínio
            "http://www.share2inspire.pt",        # Versão HTTP+www do domínio
            "http://localhost:3000",              # Porta 3000 (comum para React/Node)
            "http://localhost:5000",              # Porta 5000 (comum para Flask)
            "http://localhost:5500",              # Porta 5500 (comum para Live Server no VS Code)
            "http://localhost:8080",              # Porta 8080 (comum para http-server)
            "http://127.0.0.1:3000",              # Alternativas com IP local
            "http://127.0.0.1:5000",
            "http://127.0.0.1:5500",
            "http://127.0.0.1:8080"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "supports_credentials": True
    }
})

# Configurar chave secreta
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24).hex())

# Middleware global para garantir cabeçalhos CORS em todas as respostas
@app.after_request
def add_cors_headers(response):
    # Verificar se o cabeçalho já existe antes de adicionar
    if 'Access-Control-Allow-Origin' not in response.headers:
        response.headers.add('Access-Control-Allow-Origin', 'https://share2inspire.pt')
    if 'Access-Control-Allow-Headers' not in response.headers:
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    if 'Access-Control-Allow-Methods' not in response.headers:
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    if 'Access-Control-Allow-Credentials' not in response.headers:
        response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Função para tratar preflight requests
def handle_cors_preflight():
    """
    Trata requisições OPTIONS para CORS
    """
    response = jsonify({"success": True})
    response.headers.add('Access-Control-Allow-Origin', 'https://share2inspire.pt')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response, 200

# Rota global para OPTIONS
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    """
    Handler global para todas as requisições OPTIONS
    """
    return handle_cors_preflight()

# Importar e registar blueprints
try:
    from src.routes.feedback import feedback_bp
    app.register_blueprint(feedback_bp, url_prefix='/api/feedback')
    logger.info("Blueprint de feedback registado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de feedback: {str(e)}")

try:
    # Importar o blueprint de payment
    from src.routes.payment import payment_bp
    app.register_blueprint(payment_bp, url_prefix='/api/payment')
    logger.info("Blueprint de payment registado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de payment: {str(e)}")

try:
    # Importar o blueprint de hr_downloads
    from src.routes.hr_downloads import hr_downloads_bp
    app.register_blueprint(hr_downloads_bp, url_prefix='/api')
    logger.info("Blueprint de hr_downloads registado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de hr_downloads: {str(e)}")

# Rota de teste/saúde
@app.route('/')
def health_check():
    return {
        "status": "online",
        "message": "API Share2Inspire em funcionamento",
        "version": "1.0.0"
    }

# Rota para debug de requisições
@app.route('/debug', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def debug_request():
    """
    Endpoint para debug de requisições
    """
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    result = {
        "method": request.method,
        "headers": dict(request.headers),
        "url": request.url,
        "path": request.path,
        "args": dict(request.args),
        "form": dict(request.form),
        "json": request.get_json(silent=True),
        "data": request.data.decode('utf-8') if request.data else None
    }
    
    return jsonify(result), 200

# Imprimir variáveis de ambiente disponíveis
logger.info("=== VARIÁVEIS DE AMBIENTE DISPONÍVEIS ===")
for key in ["BREVO_API_KEY", "IFTHENPAY_API_KEY", "IFTHENPAY_CALLBACK_SECRET", 
           "IFTHENPAY_MBWAY_KEY", "IFTHENPAY_PAYSHOP_KEY", "IFTHENPAY_MULTIBANCO_ENTITY", 
           "IFTHENPAY_MULTIBANCO_SUBENTITY", "FLASK_SECRET_KEY"]:
    logger.info(f"{key}: {'DEFINIDA' if os.getenv(key) else 'NÃO DEFINIDA'}")

# Se executado diretamente
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "False").lower() == "true")
