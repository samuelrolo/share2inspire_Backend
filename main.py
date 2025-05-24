#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Aplicação principal do backend Share2Inspire
Versão ultra-robusta com configuração CORS corrigida para aceitar qualquer origem
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

# Configuração CORS ultra-permissiva para resolver problemas de CORS
CORS(app, 
     resources={r"/*": {"origins": "*"}}, 
     supports_credentials=True,
     allow_headers=["*"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"])

# Configurar chave secreta
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24).hex())

# Middleware global para garantir cabeçalhos CORS em todas as respostas
@app.after_request
def add_cors_headers(response):
    # Adicionar cabeçalhos CORS a todas as respostas
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With,*')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS,PATCH,HEAD')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Função para tratar preflight requests
def handle_cors_preflight():
    """
    Trata requisições OPTIONS para CORS
    """
    response = jsonify({"success": True})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With,*')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS,PATCH,HEAD')
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
