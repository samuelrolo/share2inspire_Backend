import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Importar Blueprints
from routes.booking import booking_bp
from routes.payment import payment_bp
from routes.services import services_bp

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Criar aplicação Flask
app = Flask(__name__)
CORS(app)

# === CONFIGURAÇÕES ===
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')

# === REGISTAR BLUEPRINTS ===
app.register_blueprint(booking_bp)
app.register_blueprint(payment_bp, url_prefix='/api/ifthenpay')
app.register_blueprint(services_bp)

# Nota: O frontend parece chamar /api/ifthenpay/... mas o blueprint payment.py não define url_prefix
# O payment.py define rotas como /initiate, /callback.
# Se o frontend chama /api/ifthenpay/multibanco, e o payment.py tem create_multibanco_payment mas a rota é /initiate...
# Espera, vamos verificar as rotas originais em main.py vs payment.py.

# main.py original:
# /api/ifthenpay/multibanco -> process_multibanco_payment
# /api/ifthenpay/mbway -> process_mbway_payment
# /api/ifthenpay/payshop -> process_payshop_payment

# payment.py novo:
# /initiate (POST) -> recebe 'paymentMethod' e despacha.
# ISTO É UMA MUDANÇA DE API. O frontend pode quebrar se estiver à espera de endpoints específicos.
# O payment.py parece ser uma versão "melhorada" mas genérica.
# O main.py tinha endpoints específicos.

# Se eu substituir main.py pelo uso de payment.py, tenho de garantir que as rotas batem certo ou que o frontend é atualizado.
# Como não posso ver o frontend (está noutra pasta fora do workspace ativo? Não, "website S2I" parece ser a raiz, e backend é subpasta).
# O user disse "Analisar backend".
# O payment.py tem:
# @payment_bp.route('/initiate', methods=['POST', 'OPTIONS'])
#
# Se eu usar o payment.py como está, perco os endpoints específicos /api/ifthenpay/multibanco, etc.
# VOU ADAPTAR O main.py PARA MANTER A COMPATIBILIDADE OU ADAPTAR O payment.py.
# O payment.py parece mais robusto.
# Vou registar o payment_bp e TAMBÉM adicionar rotas de compatibilidade no main.py ou no payment.py.
# Melhor: Vou editar o payment.py para incluir os endpoints específicos que existiam no main.py, chamando a lógica nova.
# Mas espere, o payment.py já tem lógica de 'normalize_payment_data'.
#
# Vamos olhar para o main.py original de novo.
# Ele chama create_multibanco_payment(amount, order_id).
# O payment.py tem create_multibanco_payment(data) onde data é um dict.
#
# Vou manter o main.py limpo e mover a lógica de compatibilidade para o payment.py se necessário, 
# mas por agora, vou assumir que o payment.py é a "nova versão" que se pretende usar.
# CONTUDO, se o frontend chama /api/ifthenpay/multibanco, vai dar 404.
#
# O user pediu "melhorias". Quebrar o frontend não é uma melhoria.
# Vou verificar se consigo manter as rotas antigas usando o payment.py.
#
# Vou editar o payment.py para adicionar as rotas legadas.
# Mas primeiro, vamos escrever o main.py básico.

# === ROTAS DE SAÚDE ===

@app.route('/')
def health():
    """Endpoint de saúde"""
    return jsonify({
        "status": "online",
        "message": "Share2Inspire Backend - Modularizado"
    })

@app.route('/health')
def health_check():
    """Health check detalhado"""
    return jsonify({
        "status": "healthy",
        "service": "Share2Inspire Backend",
        "version": "2.0.0"
    })

# === TRATAMENTO DE ERROS ===

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Endpoint não encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Erro interno do servidor"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
