# /home/ubuntu/share2inspire_Backend/src/payment.py

import os
import json
import uuid
import logging
import requests
from flask import Blueprint, request, jsonify, current_app
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

payment_bp = Blueprint("payment", __name__, url_prefix="/api/payment")

# Configurações Ifthenpay
IFTHENPAY_API_KEY = os.getenv("IFTHENPAY_API_KEY")
IFTHENPAY_MBWAY_KEY = os.getenv("IFTHENPAY_MBWAY_KEY")
IFTHENPAY_MULTIBANCO_ENTITY = os.getenv("IFTHENPAY_MULTIBANCO_ENTITY")
IFTHENPAY_MULTIBANCO_SUBENTITY = os.getenv("IFTHENPAY_MULTIBANCO_SUBENTITY")
IFTHENPAY_PAYSHOP_KEY = os.getenv("IFTHENPAY_PAYSHOP_KEY")
IFTHENPAY_CALLBACK_SECRET = os.getenv("IFTHENPAY_CALLBACK_SECRET")
IFTHENPAY_CALLBACK_URL = os.getenv("IFTHENPAY_CALLBACK_URL", "https://share2inspire.pt/api/payment/callback" )

# Verificar configurações
if not all([IFTHENPAY_API_KEY, IFTHENPAY_MULTIBANCO_ENTITY, IFTHENPAY_MULTIBANCO_SUBENTITY]):
    logger.error("Configurações Ifthenpay incompletas. Verifique as variáveis de ambiente.")

# URLs da API Ifthenpay
IFTHENPAY_BASE_URL = "https://ifthenpay.com/api/v1"
IFTHENPAY_MULTIBANCO_URL = f"{IFTHENPAY_BASE_URL}/multibanco/reference"
IFTHENPAY_MBWAY_URL = f"{IFTHENPAY_BASE_URL}/mbway/payment"
IFTHENPAY_PAYSHOP_URL = f"{IFTHENPAY_BASE_URL}/payshop/reference"

@payment_bp.route("/initiate", methods=["POST"] )
def initiate_payment():
    """
    Inicia um novo pagamento com base no método selecionado.
    Métodos suportados: mb (Multibanco), mbway (MB WAY), payshop (Payshop)
    """
    try:
        data = request.get_json()
        logger.info(f"Dados de pagamento recebidos: {json.dumps(data, indent=2)}")

        if not data:
            logger.warning("Nenhum dado recebido no corpo da requisição")
            return jsonify({"error": "Nenhum dado recebido", "success": False}), 400

        # Validação de campos obrigatórios
        required_fields = ["paymentMethod", "amount", "orderId"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            logger.warning(f"Campos obrigatórios em falta: {', '.join(missing_fields)}")
            return jsonify({
                "error": f"Campos obrigatórios em falta: {', '.join(missing_fields)}",
                "success": False
            }), 400

        payment_method = data.get("paymentMethod", "mb").lower()
        amount = float(data.get("amount", 0))
        order_id = data.get("orderId", f"ORDER_{uuid.uuid4().hex[:8]}")
        
        # Validar valor
        if amount <= 0:
            logger.warning(f"Valor inválido: {amount}")
            return jsonify({"error": "Valor de pagamento inválido", "success": False}), 400

        # Processar pagamento com base no método
        if payment_method == "mb" or payment_method == "multibanco":
            return create_multibanco_reference(data, amount, order_id)
        elif payment_method == "mbway":
            return create_mbway_payment(data, amount, order_id)
        elif payment_method == "payshop":
            return create_payshop_reference(data, amount, order_id)
        else:
            logger.warning(f"Método de pagamento não suportado: {payment_method}")
            return jsonify({"error": "Método de pagamento não suportado", "success": False}), 400
            
    except Exception as e:
        logger.exception(f"Erro ao iniciar pagamento: {str(e)}")
        return jsonify({"error": "Erro ao processar pagamento", "success": False}), 500

def create_multibanco_reference(data, amount, order_id):
    """
    Cria uma referência Multibanco para pagamento
    """
    try:
        # Preparar dados para API Ifthenpay
        payload = {
            "entity": IFTHENPAY_MULTIBANCO_ENTITY,
            "subEntity": IFTHENPAY_MULTIBANCO_SUBENTITY,
            "amount": amount,
            "orderId": order_id,
            "description": data.get("description", f"Pagamento Share2Inspire #{order_id}"),
            "callbackUrl": IFTHENPAY_CALLBACK_URL
        }
        
        # Adicionar chave anti-phishing se disponível
        if IFTHENPAY_CALLBACK_SECRET:
            payload["callbackSecret"] = IFTHENPAY_CALLBACK_SECRET
        
        # Enviar requisição para API Ifthenpay
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {IFTHENPAY_API_KEY}"
        }
        
        logger.info(f"Enviando requisição para criar referência Multibanco: {json.dumps(payload, indent=2)}")
        response = requests.post(IFTHENPAY_MULTIBANCO_URL, json=payload, headers=headers)
        
        # Processar resposta
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Referência Multibanco criada com sucesso: {json.dumps(result, indent=2)}")
            
            # Salvar dados do pagamento (em produção, salvar em banco de dados)
            # save_payment_data(order_id, "multibanco", amount, result)
            
            return jsonify({
                "success": True,
                "method": "mb",
                "entity": result.get("entity"),
                "reference": result.get("reference"),
                "amount": amount,
                "orderId": order_id
            }), 200
        else:
            logger.error(f"Erro ao criar referência Multibanco: {response.status_code} - {response.text}")
            return jsonify({
                "error": "Erro ao gerar referência Multibanco",
                "details": response.text,
                "success": False
            }), response.status_code
            
    except Exception as e:
        logger.exception(f"Erro ao criar referência Multibanco: {str(e)}")
        return jsonify({"error": "Erro ao gerar referência Multibanco", "success": False}), 500

def create_mbway_payment(data, amount, order_id):
    """
    Cria um pagamento MB WAY
    """
    try:
        # Validar número de telefone
        phone = data.get("customerPhone")
        if not phone or not phone.isdigit() or len(phone) < 9:
            logger.warning(f"Número de telefone inválido para MB WAY: {phone}")
            return jsonify({"error": "Número de telefone inválido para MB WAY", "success": False}), 400
        
        # Formatar telefone (remover prefixo +351 se existir)
        if phone.startswith("+351"):
            phone = phone[4:]
        elif phone.startswith("00351"):
            phone = phone[5:]
        
        # Preparar dados para API Ifthenpay
        payload = {
            "mbwayKey": IFTHENPAY_MBWAY_KEY,
            "amount": amount,
            "phone": phone,
            "orderId": order_id,
            "description": data.get("description", f"Pagamento Share2Inspire #{order_id}"),
            "callbackUrl": IFTHENPAY_CALLBACK_URL
        }
        
        # Adicionar chave anti-phishing se disponível
        if IFTHENPAY_CALLBACK_SECRET:
            payload["callbackSecret"] = IFTHENPAY_CALLBACK_SECRET
        
        # Enviar requisição para API Ifthenpay
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {IFTHENPAY_API_KEY}"
        }
        
        logger.info(f"Enviando requisição para criar pagamento MB WAY: {json.dumps(payload, indent=2)}")
        response = requests.post(IFTHENPAY_MBWAY_URL, json=payload, headers=headers)
        
        # Processar resposta
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Pagamento MB WAY criado com sucesso: {json.dumps(result, indent=2)}")
            
            # Salvar dados do pagamento (em produção, salvar em banco de dados)
            # save_payment_data(order_id, "mbway", amount, result)
            
            return jsonify({
                "success": True,
                "method": "mbway",
                "reference": result.get("referenceId"),
                "amount": amount,
                "orderId": order_id,
                "phone": phone
            }), 200
        else:
            logger.error(f"Erro ao criar pagamento MB WAY: {response.status_code} - {response.text}")
            return jsonify({
                "error": "Erro ao gerar pagamento MB WAY",
                "details": response.text,
                "success": False
            }), response.status_code
            
    except Exception as e:
        logger.exception(f"Erro ao criar pagamento MB WAY: {str(e)}")
        return jsonify({"error": "Erro ao gerar pagamento MB WAY", "success": False}), 500

def create_payshop_reference(data, amount, order_id):
    """
    Cria uma referência Payshop para pagamento
    """
    try:
        # Preparar dados para API Ifthenpay
        payload = {
            "payshopKey": IFTHENPAY_PAYSHOP_KEY,
            "amount": amount,
            "orderId": order_id,
            "description": data.get("description", f"Pagamento Share2Inspire #{order_id}"),
            "callbackUrl": IFTHENPAY_CALLBACK_URL,
            # Validade padrão de 5 dias (em segundos)
            "validDays": data.get("validDays", 5)
        }
        
        # Adicionar chave anti-phishing se disponível
        if IFTHENPAY_CALLBACK_SECRET:
            payload["callbackSecret"] = IFTHENPAY_CALLBACK_SECRET
        
        # Enviar requisição para API Ifthenpay
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {IFTHENPAY_API_KEY}"
        }
        
        logger.info(f"Enviando requisição para criar referência Payshop: {json.dumps(payload, indent=2)}")
        response = requests.post(IFTHENPAY_PAYSHOP_URL, json=payload, headers=headers)
        
        # Processar resposta
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Referência Payshop criada com sucesso: {json.dumps(result, indent=2)}")
            
            # Salvar dados do pagamento (em produção, salvar em banco de dados)
            # save_payment_data(order_id, "payshop", amount, result)
            
            return jsonify({
                "success": True,
                "method": "payshop",
                "reference": result.get("reference"),
                "amount": amount,
                "orderId": order_id,
                "validity": result.get("expirationDate")
            }), 200
        else:
            logger.error(f"Erro ao criar referência Payshop: {response.status_code} - {response.text}")
            return jsonify({
                "error": "Erro ao gerar referência Payshop",
                "details": response.text,
                "success": False
            }), response.status_code
            
    except Exception as e:
        logger.exception(f"Erro ao criar referência Payshop: {str(e)}")
        return jsonify({"error": "Erro ao gerar referência Payshop", "success": False}), 500

@payment_bp.route("/callback", methods=["POST"])
def payment_callback():
    """
    Endpoint para receber callbacks de pagamento da Ifthenpay
    """
    try:
        data = request.get_json()
        logger.info(f"Callback de pagamento recebido: {json.dumps(data, indent=2)}")

        if not data:
            logger.warning("Nenhum dado recebido no callback")
            return jsonify({"error": "Nenhum dado recebido"}), 400

        # Validar callback com chave anti-phishing
        if IFTHENPAY_CALLBACK_SECRET:
            received_secret = data.get("callbackSecret")
            if received_secret != IFTHENPAY_CALLBACK_SECRET:
                logger.warning(f"Chave anti-phishing inválida: {received_secret}")
                return jsonify({"error": "Chave anti-phishing inválida"}), 403

        # Extrair dados do callback
        payment_method = data.get("type", "unknown").lower()
        order_id = data.get("orderId")
        reference = data.get("reference") or data.get("referenceId")
        amount = data.get("amount")
        status = data.get("status", "unknown").lower()
        
        # Validar dados mínimos
        if not all([order_id, reference, amount]):
            logger.warning("Dados de callback incompletos")
            return jsonify({"error": "Dados de callback incompletos"}), 400
        
        # Processar pagamento com base no status
        if status == "paid" or status == "completed":
            # Em produção, atualizar status do pagamento no banco de dados
            # update_payment_status(order_id, "paid")
            
            # Em produção, enviar email de confirmação ao cliente
            # send_payment_confirmation_email(order_id)
            
            logger.info(f"Pagamento {payment_method} confirmado para pedido {order_id}")
            return jsonify({"success": True, "message": "Pagamento processado com sucesso"}), 200
        else:
            logger.warning(f"Status de pagamento não reconhecido: {status}")
            return jsonify({"success": False, "message": f"Status não processado: {status}"}), 200
            
    except Exception as e:
        logger.exception(f"Erro ao processar callback de pagamento: {str(e)}")
        return jsonify({"error": "Erro ao processar callback"}), 500

@payment_bp.route("/status/<order_id>", methods=["GET"])
def payment_status(order_id):
    """
    Verifica o status de um pagamento
    Em produção, consultar banco de dados
    """
    try:
        # Em produção, consultar status do pagamento no banco de dados
        # payment = get_payment_by_order_id(order_id)
        
        # Simulação para desenvolvimento
        payment = {
            "orderId": order_id,
            "status": "pending",
            "method": "multibanco",
            "amount": 30.0,
            "reference": "123456789",
            "entity": "11111"
        }
        
        return jsonify({
            "success": True,
            "payment": payment
        }), 200
            
    except Exception as e:
        logger.exception(f"Erro ao consultar status do pagamento: {str(e)}")
        return jsonify({"error": "Erro ao consultar status do pagamento", "success": False}), 500

# Funções auxiliares para persistência de dados (implementar em produção)
def save_payment_data(order_id, method, amount, data):
    """
    Salva dados do pagamento em banco de dados
    Implementar em produção
    """
    logger.info(f"Salvando dados de pagamento para pedido {order_id}")
    # Implementação para banco de dados

def update_payment_status(order_id, status):
    """
    Atualiza status do pagamento em banco de dados
    Implementar em produção
    """
    logger.info(f"Atualizando status do pagamento para pedido {order_id}: {status}")
    # Implementação para banco de dados

def send_payment_confirmation_email(order_id):
    """
    Envia email de confirmação de pagamento
    Implementar em produção
    """
    logger.info(f"Enviando email de confirmação para pedido {order_id}")
    # Implementação para envio de email
