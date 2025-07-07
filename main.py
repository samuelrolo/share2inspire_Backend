#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação principal do backend Share2Inspire
Versão CORRIGIDA com importações diretas dos módulos
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
    response = jsonify({"success": True})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response, 200

# Importar e registar blueprints - CORRIGIDO para importações diretas
try:
    from fedback import feedback_bp
    app.register_blueprint(feedback_bp, url_prefix='/api/feedback')
    logger.info("Blueprint de feedback registado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de feedback: {str(e)}")

try:
    from payment import payment_bp
    app.register_blueprint(payment_bp, url_prefix='/api/payment')
    logger.info("Blueprint de payment registado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de payment: {str(e)}")

try:
    from ifthenpay import ifthenpay_bp
    app.register_blueprint(ifthenpay_bp, url_prefix='/api/ifthenpay')
    logger.info("Blueprint de IFTHENPAY registado com sucesso em /api/ifthenpay")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de ifthenpay: {str(e)}")

try:
    from email_service import email_bp
    app.register_blueprint(email_bp, url_prefix='/api/email')
    logger.info("Blueprint de EMAIL registado com sucesso em /api/email")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de email: {str(e)}")

try:
    from booking import booking_bp
    app.register_blueprint(booking_bp, url_prefix='/api/booking')
    logger.info("Blueprint de BOOKING registado com sucesso em /api/booking")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de booking: {str(e)}")

try:
    from user import user_bp
    app.register_blueprint(user_bp, url_prefix='/api/user')
    logger.info("Blueprint de USER registado com sucesso em /api/user")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de user: {str(e)}")

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
            "feedback": "disponível em /api/feedback/*",
            "booking": "disponível em /api/booking/*",
            "user": "disponível em /api/user/*"
        },
        "cors": "enabled for all origins"
    }

# Rota para debug
@app.route('/debug', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def debug_request():
    if request.method == 'OPTIONS':
        return options_handler()
    
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
        
        # Verificar serviços
        try:
            from email_service import email_bp
            status["services"]["email"] = "online"
        except ImportError:
            status["services"]["email"] = "offline"
            
        try:
            from ifthenpay import ifthenpay_bp
            status["services"]["ifthenpay"] = "online"
        except ImportError:
            status["services"]["ifthenpay"] = "offline"
            
        # Verificar variáveis de ambiente
        env_status = {}
        critical_vars = [
            "BREVO_API_KEY",
            "IFTHENPAY_MBWAY_KEY", 
            "IFTHENPAY_MULTIBANCO_KEY",
            "IFTHENPAY_PAYSHOP_KEY"
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

# Log das variáveis de ambiente
logger.info("=== VERIFICAÇÃO DE VARIÁVEIS DE AMBIENTE ===")
env_vars_to_check = [
    "BREVO_API_KEY",
    "BREVO_SENDER_EMAIL", 
    "BREVO_SENDER_NAME",
    "IFTHENPAY_MBWAY_KEY",
    "IFTHENPAY_MULTIBANCO_KEY",
    "IFTHENPAY_PAYSHOP_KEY"
]

for key in env_vars_to_check:
    value = os.getenv(key)
    if value:
        masked_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
        logger.info(f"{key}: DEFINIDA ({masked_value})")
    else:
        logger.warning(f"{key}: NÃO DEFINIDA")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    
    logger.info(f"Iniciando servidor na porta {port}")
    logger.info(f"Modo debug: {debug_mode}")
    logger.info("Servidor configurado para 0.0.0.0 (todas as interfaces)")
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)

