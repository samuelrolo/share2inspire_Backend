#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação principal do backend Share2Inspire
Versão CORRIGIDA com blueprints de email_service e ifthenpay - URL PREFIX CORRIGIDO
"""

import os
import logging
from flask import Flask, Blueprint, jsonify, request, send_from_directory
from flask_cors import CORS 
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Criar aplicação Flask
app = Flask(__name__)

# Configuração CORS corrigida
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://share2inspire.pt",
            "http://share2inspire.pt",
            "https://www.share2inspire.pt",
            "http://www.share2inspire.pt",
            "http://localhost:3000",
            "http://localhost:5000",
            "http://localhost:5500",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
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
    if 'Access-Control-Allow-Origin' not in response.headers:
        response.headers.add('Access-Control-Allow-Origin', '*')
    if 'Access-Control-Allow-Headers' not in response.headers:
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    if 'Access-Control-Allow-Methods' not in response.headers:
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    if 'Access-Control-Allow-Credentials' not in response.headers:
        response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Função para tratar preflight requests
def handle_cors_preflight():
    response = jsonify({"success": True})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response, 200

@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    return handle_cors_preflight()

# Importar e registar blueprints existentes
try:
    # CORRIGIDO: Caminho de importação e nome do módulo
    from src.routes.feedback import feedback_bp
    app.register_blueprint(feedback_bp, url_prefix='/api/feedback')
    logger.info("Blueprint de feedback registado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de feedback: {str(e)}")

try:
    # CORRIGIDO: Caminho de importação
    from src.routes.payment import payment_bp
    app.register_blueprint(payment_bp, url_prefix='/api/payment')
    logger.info("Blueprint de payment registado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de payment: {str(e)}")

try:
    # CORRIGIDO: Caminho de importação
    from src.routes.ifthenpay import ifthenpay_bp
    app.register_blueprint(ifthenpay_bp, url_prefix='/api/ifthenpay')
    logger.info("Blueprint de IFTHENPAY registado com sucesso em /api/ifthenpay")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de ifthenpay: {str(e)}")
    logger.error("ATENÇÃO: Serviços de pagamento Ifthenpay não estarão disponíveis!")

# CORRIGIDO: Import da blueprint de email_service
try:
    # CORRIGIDO: Caminho de importação
    from src.routes.email import email_bp
    app.register_blueprint(email_bp, url_prefix='/api/email')
    logger.info("Blueprint de EMAIL registado com sucesso em /api/email")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de email: {str(e)}")
    logger.error("ATENÇÃO: Serviços de email não estarão disponíveis!")

# Rota de teste/saúde
@app.route('/')
def health_check():
    return {
        "status": "online",
        "message": "API Share2Inspire em funcionamento",
        "version": "2.1.0",
        "services": {
            "email": "disponível em /api/email/*",
            "ifthenpay": "disponível em /api/ifthenpay/*",
            "payment": "disponível em /api/payment/*",
            "feedback": "disponível em /api/feedback/*"
        },
        "cors": "enabled for all origins"
    }

# Rota para debug de requisições
@app.route('/debug', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def debug_request():
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

@app.route('/status')
def service_status():
    try:
        from datetime import datetime
        status = {
            "timestamp": str(datetime.now()),
            "services": {}
        }
        # CORRIGIDO: Caminhos de importação para o status check
        try:
            from src.routes.email import email_bp
            status["services"]["email"] = "online"
        except ImportError:
            status["services"]["email"] = "offline"
        try:
            from src.routes.ifthenpay import ifthenpay_bp
            status["services"]["ifthenpay"] = "online"
        except ImportError:
            status["services"]["ifthenpay"] = "offline"
        env_status = {}
        critical_vars = [
            "BREVO_API_KEY",
            "IFTHENPAY_MBWAY_KEY",
            "IFTHENPAY_MULTIBANCO_KEY",
            "IFTHENPAY_PAYSHOP_KEY",
            "FLASK_SECRET_KEY"
        ]
        for var in critical_vars:
            env_status[var] = "DEFINIDA" if os.getenv(var) else "NÃO DEFINIDA"
        status["environment"] = env_status
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Erro no status check: {str(e)}")
        return jsonify({
            "error": "Erro ao verificar status dos serviços",
            "details": str(e)
        }), 500

# Imprimir variáveis de ambiente disponíveis
logger.info("=== VARIÁVEIS DE AMBIENTE DISPONÍVEIS ===")
env_vars_to_check = [
    "BREVO_API_KEY",
    "BREVO_SENDER_EMAIL",
    "BREVO_SENDER_NAME",
    "IFTHENPAY_MBWAY_KEY",
    "IFTHENPAY_MULTIBANCO_KEY",
    "IFTHENPAY_PAYSHOP_KEY",
    "IFTHENPAY_CALLBACK_SECRET",
    "FLASK_SECRET_KEY"
]
for key in env_vars_to_check:
    value = os.getenv(key)
    if value:
        if len(value) > 10:
            masked_value = value[:4] + "..." + value[-4:]
        else:
            masked_value = "***"
        logger.info(f"{key}: DEFINIDA ({masked_value})")
    else:
        logger.info(f"{key}: NÃO DEFINIDA")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    logger.info(f"Iniciando servidor na porta {port}")
    logger.info(f"Modo debug: {debug_mode}")
    logger.info("URL PREFIX CORRIGIDO: /api/ifthenpay")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)

