"""
Share2Inspire Backend - VERSÃO COM EMAIL CORRIGIDO
Mantém a funcionalidade de email que funcionava + correções Ifthenpay
"""

import os
import logging
<<<<<<< Updated upstream
from flask import Flask, jsonify
=======
import requests
from datetime import datetime
from flask import Flask, request, jsonify
>>>>>>> Stashed changes
from flask_cors import CORS
from dotenv import load_dotenv

<<<<<<< Updated upstream
<<<<<<< Updated upstream
# Importar Blueprints
from routes.booking import booking_bp
from routes.payment import payment_bp
from routes.services import services_bp

=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Criar aplicação Flask
app = Flask(__name__)
CORS(app)

# === ROTAS DE SAÚDE ===

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
@app.route('/')
def health_check():
    return jsonify({
        "message": "Share2Inspire Backend - Email Corrigido",
        "status": "online",
        "timestamp": datetime.now().isoformat()
    })

=======
@app.route('/')
def health_check():
    return jsonify({
        "message": "Share2Inspire Backend - Email Corrigido",
        "status": "online",
        "timestamp": datetime.now().isoformat()
    })

>>>>>>> Stashed changes
=======
@app.route('/')
def health_check():
    return jsonify({
        "message": "Share2Inspire Backend - Email Corrigido",
        "status": "online",
        "timestamp": datetime.now().isoformat()
    })

>>>>>>> Stashed changes
@app.route('/api/health')
def api_health():
    return jsonify({
        "service": "share2inspire-backend",
        "status": "healthy",
        "version": "email-fixed",
        "timestamp": datetime.now().isoformat()
    })

# === ROTAS DE EMAIL (CORRIGIDAS) ===

@app.route('/api/email/kickstart', methods=['POST'])
def send_kickstart_email():
    try:
        data = request.get_json()
        logger.info(f"Dados recebidos para email: {data}")
        
        # Validação mais flexível
        if not data:
            return jsonify({"success": False, "error": "Dados não recebidos"}), 400
            
        email = data.get('email')
        name = data.get('name')
        
        if not email:
            return jsonify({"success": False, "error": "Email obrigatório"}), 400
            
        if not name:
            return jsonify({"success": False, "error": "Nome obrigatório"}), 400
        
        # Enviar email via Brevo (função simplificada)
        result = send_brevo_email_simple(email, name, data)
        
        if result['success']:
            logger.info(f"Email de Kickstart Pro enviado para {email}")
            return jsonify({"success": True, "message": "Email enviado com sucesso"})
        else:
            logger.error(f"Erro ao enviar email: {result['error']}")
            return jsonify({"success": False, "error": result['error']}), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint de email: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

def send_brevo_email_simple(to_email, to_name, form_data):
    """Enviar email via Brevo - versão simplificada"""
    try:
        api_key = os.getenv('BREVO_API_KEY')
        if not api_key:
            return {"success": False, "error": "Chave API Brevo não configurada"}
        
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            'accept': 'application/json',
            'api-key': api_key,
            'content-type': 'application/json'
        }
        
        # Template simples
        subject = "Confirmação - Kickstart Pro Share2Inspire"
        html_content = f"""
        <h2>Obrigado pelo seu interesse no Kickstart Pro!</h2>
        <p>Olá {to_name},</p>
        <p>Recebemos a sua marcação para o Kickstart Pro. Entraremos em contacto brevemente.</p>
        <p><strong>Detalhes:</strong></p>
        <ul>
            <li>Nome: {to_name}</li>
            <li>Email: {to_email}</li>
            <li>Data: {form_data.get('date', 'A definir')}</li>
            <li>Duração: {form_data.get('duration', '30 minutos')}</li>
        </ul>
        <p>Cumprimentos,<br>Equipa Share2Inspire</p>
        """
        
        payload = {
            "sender": {
                "name": "Share2Inspire",
                "email": "noreply@share2inspire.pt"
            },
            "to": [{"email": to_email, "name": to_name}],
            "subject": subject,
            "htmlContent": html_content
        }
        
        logger.info(f"Enviando email para {to_email}")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 201:
            return {"success": True, "message": "Email enviado"}
        else:
            logger.error(f"Erro Brevo {response.status_code}: {response.text}")
            return {"success": False, "error": f"Erro Brevo: {response.status_code}"}
        
    except Exception as e:
        logger.error(f"Erro ao enviar email: {str(e)}")
        return {"success": False, "error": str(e)}
>>>>>>> Stashed changes

# === ROTAS IFTHENPAY (CORRIGIDAS) ===

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
@app.route('/api/ifthenpay/multibanco', methods=['POST'])
def create_multibanco_reference():
    try:
        data = request.get_json()
        logger.info(f"Dados recebidos para Multibanco: {data}")
        
        if not data.get('amount') or not data.get('orderId'):
            return jsonify({"success": False, "error": "Amount e orderId obrigatórios"}), 400
        
        result = create_multibanco_payment(
            amount=float(data['amount']),
            order_id=data['orderId']
        )
        
        logger.info(f"Resultado Multibanco: {result}")
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint Multibanco: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/ifthenpay/mbway', methods=['POST'])
def create_mbway_payment_endpoint():
    try:
        data = request.get_json()
        logger.info(f"Dados recebidos para MB WAY: {data}")
        
        required_fields = ['amount', 'orderId', 'mobileNumber']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"success": False, "error": f"Campo {field} obrigatório"}), 400
        
        result = create_mbway_payment(
            amount=float(data['amount']),
            phone=data['mobileNumber'],
            order_id=data['orderId']
        )
        
        logger.info(f"Resultado MB WAY: {result}")
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Erro no endpoint MB WAY: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/ifthenpay/payshop', methods=['POST'])
def create_payshop_reference():
    try:
        data = request.get_json()
        logger.info(f"Dados recebidos para Payshop: {data}")
        
        if not data.get('amount') or not data.get('orderId'):
            return jsonify({"success": False, "error": "Amount e orderId obrigatórios"}), 400
        
        result = create_payshop_payment(
            amount=float(data['amount']),
            order_id=data['orderId']
        )
        
        logger.info(f"Resultado Payshop: {result}")
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint Payshop: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# === FUNCIONALIDADES IFTHENPAY ===

def create_multibanco_payment(amount, order_id):
    """Criar pagamento Multibanco via Ifthenpay"""
    try:
        key = os.getenv('IFTHENPAY_MULTIBANCO_KEY')
        if not key:
            raise ValueError("Chave Multibanco não configurada")
        
        url = "https://api.ifthenpay.com/multibanco/reference/init"
        data = {
            'mbKey': key,
            'orderId': order_id,
            'amount': f"{amount:.2f}"
        }
        
        logger.info(f"Chamando Multibanco API: {url}")
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Resposta Multibanco: {result}")
        
        return {
            "success": True,
            "entity": result.get('Entity'),
            "reference": result.get('Reference'),
            "amount": amount,
            "orderId": result.get('OrderId'),
            "requestId": result.get('RequestId'),
            "status": result.get('Status')
        }
        
    except Exception as e:
        logger.error(f"Erro Multibanco: {str(e)}")
        return {"success": False, "error": str(e)}

def create_mbway_payment(amount, phone, order_id):
    """Criar pagamento MB WAY via Ifthenpay - CORRIGIDO"""
    try:
        key = os.getenv('IFTHENPAY_MBWAY_KEY')
        if not key:
            raise ValueError("Chave MB WAY não configurada")
        
        # URL CORRIGIDA
        url = "https://api.ifthenpay.com/mbway/payments"
        
        # Formatar telefone
        clean_phone = phone.replace(' ', '').replace('-', '').replace('+', '')
        if not clean_phone.startswith('351'):
            if clean_phone.startswith('9') and len(clean_phone) == 9:
                clean_phone = f"351{clean_phone}"
            else:
                clean_phone = f"351{clean_phone}"
        
        data = {
            'mbWayKey': key,
            'orderId': order_id,
            'amount': f"{amount:.2f}",
            'mobileNumber': clean_phone,
            'description': f"Pagamento Share2Inspire - {order_id}"
        }
        
        logger.info(f"Chamando MB WAY API: {url}")
        response = requests.post(url, json=data)
        logger.info(f"Status MB WAY: {response.status_code}")
        
        response.raise_for_status()
        result = response.json()
        logger.info(f"Resposta MB WAY: {result}")
        
        return {
            "success": True,
            "requestId": result.get('RequestId'),
            "amount": amount,
            "mobileNumber": clean_phone,
            "orderId": order_id,
            "status": result.get('Status', 'pending'),
            "message": result.get('Message', 'Pedido MB WAY enviado')
        }
        
    except Exception as e:
        logger.error(f"Erro MB WAY: {str(e)}")
        return {"success": False, "error": str(e)}

def create_payshop_payment(amount, order_id):
    """Criar pagamento Payshop via Ifthenpay"""
    try:
        key = os.getenv('IFTHENPAY_PAYSHOP_KEY')
        if not key:
            raise ValueError("Chave Payshop não configurada")
        
        url = "https://api.ifthenpay.com/payshop/reference/init"
        data = {
            'payshopKey': key,
            'orderId': order_id,
            'amount': f"{amount:.2f}"
        }
        
        logger.info(f"Chamando Payshop API: {url}")
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Resposta Payshop: {result}")
        
        return {
            "success": True,
            "reference": result.get('Reference'),
            "amount": amount,
            "orderId": result.get('OrderId'),
            "requestId": result.get('RequestId'),
            "validade": result.get('ExpiryDate')
        }
        
    except Exception as e:
        logger.error(f"Erro Payshop: {str(e)}")
        return {"success": False, "error": str(e)}

# === OUTRAS ROTAS ===

@app.route('/api/booking', methods=['POST'])
def create_booking():
    try:
        data = request.get_json()
        logger.info(f"Nova marcação: {data}")
        
        return jsonify({
            "success": True,
            "message": "Marcação criada",
            "booking_id": f"BOOK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        })
        
    except Exception as e:
        logger.error(f"Erro marcação: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
>>>>>>> Stashed changes

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
