# /home/ubuntu/share2inspire_Backend/src/payment.py
import os
import json
import uuid
import logging
import requests
from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from dotenv import load_dotenv
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

payment_bp = Blueprint("payment", __name__, url_prefix="/api/payment")

# Configurações Ifthenpay
IFTHENPAY_MBWAY_KEY = os.getenv("IFTHENPAY_MBWAY_KEY")
IFTHENPAY_MB_KEY = os.getenv("IFTHENPAY_MB_KEY")
IFTHENPAY_PAYSHOP_KEY = os.getenv("IFTHENPAY_PAYSHOP_KEY")
IFTHENPAY_CALLBACK_SECRET = os.getenv("IFTHENPAY_CALLBACK_SECRET")
IFTHENPAY_CALLBACK_URL = os.getenv("IFTHENPAY_CALLBACK_URL", "https://share2inspire-beckend.lm.r.appspot.com/api/payment/callback")

# Configurações Brevo
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
BREVO_SENDER_NAME = os.getenv("BREVO_SENDER_NAME", "Share2Inspire")
BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL", "srshare2inspire@gmail.com")

# Verificar configurações
if not all([IFTHENPAY_MBWAY_KEY, IFTHENPAY_MB_KEY, IFTHENPAY_PAYSHOP_KEY]):
    logger.error("Configurações Ifthenpay incompletas. Verifique as variáveis de ambiente.")
if not BREVO_API_KEY:
    logger.error("Configuração Brevo incompleta. Verifique a variável de ambiente BREVO_API_KEY.")

# URLs da API Ifthenpay (atualizados para a nova API)
IFTHENPAY_MBWAY_URL = "https://api.ifthenpay.com/spg/payment/mbway"
IFTHENPAY_MULTIBANCO_URL = "https://api.ifthenpay.com/multibanco/reference/init"
IFTHENPAY_PAYSHOP_URL = "https://ifthenpay.com/api/payshop/reference"

@payment_bp.route("/initiate", methods=["POST", "OPTIONS"])
@cross_origin()
def initiate_payment():
    """
    Inicia um novo pagamento com base no método selecionado.
    Métodos suportados: mb (Multibanco), mbway (MB WAY), payshop (Payshop)
    """
    # Tratar pedidos OPTIONS para CORS
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200
    
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
        # Preparar dados para API Ifthenpay (atualizado para a nova API)
        payload = {
            "mbKey": IFTHENPAY_MB_KEY,
            "orderId": order_id,
            "amount": amount,
            "description": data.get("description", f"Pagamento Share2Inspire #{order_id}"),
            "url": data.get("url", "https://share2inspire.pt"),
            "clientCode": data.get("clientCode", ""),
            "clientName": data.get("customerName", ""),
            "clientEmail": data.get("customerEmail", ""),
            "clientUsername": data.get("customerUsername", ""),
            "clientPhone": data.get("customerPhone", ""),
            "expiryDays": data.get("expiryDays", 0)  # 0 = sem expiração
        }
        
        # Enviar requisição para API Ifthenpay
        headers = {
            "Content-Type": "application/json"
        }
        
        logger.info(f"Enviando requisição para criar referência Multibanco: {json.dumps(payload, indent=2)}")
        response = requests.post(IFTHENPAY_MULTIBANCO_URL, json=payload, headers=headers)
        
        # Processar resposta
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Referência Multibanco criada com sucesso: {json.dumps(result, indent=2)}")
            
            # Salvar dados do pagamento (em produção, salvar em banco de dados)
            payment_data = {
                "orderId": order_id,
                "method": "multibanco",
                "amount": amount,
                "entity": result.get("Entity"),
                "reference": result.get("Reference"),
                "description": data.get("description", f"Pagamento Share2Inspire #{order_id}"),
                "customerName": data.get("customerName", ""),
                "customerEmail": data.get("customerEmail", ""),
                "customerPhone": data.get("customerPhone", ""),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "appointmentDate": data.get("date", ""),
                "appointmentTime": data.get("time", ""),
                "status": "pending"
            }
            
            save_payment_data(order_id, "multibanco", amount, payment_data)
            
            return jsonify({
                "success": True,
                "method": "mb",
                "entity": result.get("Entity"),
                "reference": result.get("Reference"),
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
        if not phone or len(phone) < 9:
            logger.warning(f"Número de telefone inválido para MB WAY: {phone}")
            return jsonify({"error": "Número de telefone inválido para MB WAY", "success": False}), 400
            
        # Formatar telefone (adicionar prefixo +351 se não existir)
        if not phone.startswith("+"):
            phone = f"+351{phone}"
            
        # Preparar dados para API Ifthenpay (atualizado para a nova API)
        payload = {
            "mbWayKey": IFTHENPAY_MBWAY_KEY,
            "orderId": order_id,
            "amount": amount,
            "mobileNumber": phone,
            "email": data.get("customerEmail", ""),
            "description": data.get("description", f"Pagamento Share2Inspire #{order_id}")
        }
        
        # Enviar requisição para API Ifthenpay
        headers = {
            "Content-Type": "application/json"
        }
        
        logger.info(f"Enviando requisição para criar pagamento MB WAY: {json.dumps(payload, indent=2)}")
        response = requests.post(IFTHENPAY_MBWAY_URL, json=payload, headers=headers)
        
        # Processar resposta
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Pagamento MB WAY criado com sucesso: {json.dumps(result, indent=2)}")
            
            # Salvar dados do pagamento (em produção, salvar em banco de dados)
            payment_data = {
                "orderId": order_id,
                "method": "mbway",
                "amount": amount,
                "reference": result.get("RequestId"),
                "description": data.get("description", f"Pagamento Share2Inspire #{order_id}"),
                "customerName": data.get("customerName", ""),
                "customerEmail": data.get("customerEmail", ""),
                "customerPhone": phone,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "appointmentDate": data.get("date", ""),
                "appointmentTime": data.get("time", ""),
                "status": "pending"
            }
            
            save_payment_data(order_id, "mbway", amount, payment_data)
            
            # Construir URL de redirecionamento para página de sucesso
            redirect_url = f"/pages/pagamento-sucesso.html?duration={data.get('duration', '30')}&amount={amount}&date={data.get('date', '')}&format={data.get('format', 'Online')}&reference={result.get('RequestId')}&method=mbway"
            
            return jsonify({
                "success": True,
                "method": "mbway",
                "requestId": result.get("RequestId"),
                "amount": amount,
                "orderId": order_id,
                "redirect": redirect_url
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
            "orderId": order_id,
            "amount": amount,
            "description": data.get("description", f"Pagamento Share2Inspire #{order_id}"),
            "validDays": data.get("validDays", 30)  # Validade padrão de 30 dias
        }
        
        # Enviar requisição para API Ifthenpay
        headers = {
            "Content-Type": "application/json"
        }
        
        logger.info(f"Enviando requisição para criar referência Payshop: {json.dumps(payload, indent=2)}")
        response = requests.post(IFTHENPAY_PAYSHOP_URL, json=payload, headers=headers)
        
        # Processar resposta
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Referência Payshop criada com sucesso: {json.dumps(result, indent=2)}")
            
            # Salvar dados do pagamento (em produção, salvar em banco de dados)
            payment_data = {
                "orderId": order_id,
                "method": "payshop",
                "amount": amount,
                "reference": result.get("Reference"),
                "description": data.get("description", f"Pagamento Share2Inspire #{order_id}"),
                "customerName": data.get("customerName", ""),
                "customerEmail": data.get("customerEmail", ""),
                "customerPhone": data.get("customerPhone", ""),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "appointmentDate": data.get("date", ""),
                "appointmentTime": data.get("time", ""),
                "validUntil": result.get("ValidUntil"),
                "status": "pending"
            }
            
            save_payment_data(order_id, "payshop", amount, payment_data)
            
            return jsonify({
                "success": True,
                "method": "payshop",
                "reference": result.get("Reference"),
                "amount": amount,
                "orderId": order_id,
                "validUntil": result.get("ValidUntil")
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

@payment_bp.route("/callback", methods=["GET", "POST", "OPTIONS"])
@cross_origin()
def payment_callback():
    """
    Endpoint para receber callbacks de pagamento da Ifthenpay
    """
    # Tratar pedidos OPTIONS para CORS
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200
        
    try:
        # Obter dados do callback
        if request.method == "GET":
            data = request.args.to_dict()
        else:
            data = request.get_json() or request.form.to_dict()
            
        logger.info(f"Callback de pagamento recebido: {json.dumps(data, indent=2)}")
        
        # Validar dados do callback
        if not data:
            logger.warning("Nenhum dado recebido no callback")
            return jsonify({"error": "Nenhum dado recebido"}), 400
            
        # Processar callback com base no método de pagamento
        payment_method = data.get("payment_type", "").lower()
        
        if payment_method == "mbway":
            return process_mbway_callback(data)
        elif payment_method == "mb" or payment_method == "multibanco":
            return process_multibanco_callback(data)
        elif payment_method == "payshop":
            return process_payshop_callback(data)
        else:
            logger.warning(f"Método de pagamento não reconhecido no callback: {payment_method}")
            return jsonify({"error": "Método de pagamento não reconhecido"}), 400
            
    except Exception as e:
        logger.exception(f"Erro ao processar callback de pagamento: {str(e)}")
        return jsonify({"error": "Erro ao processar callback"}), 500

def process_mbway_callback(data):
    """
    Processa callback de pagamento MB WAY
    """
    try:
        # Validar dados do callback
        required_fields = ["requestId", "status"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            logger.warning(f"Campos obrigatórios em falta no callback MB WAY: {', '.join(missing_fields)}")
            return jsonify({
                "error": f"Campos obrigatórios em falta: {', '.join(missing_fields)}"
            }), 400
            
        request_id = data.get("requestId")
        status = data.get("status")
        
        # Atualizar status do pagamento (em produção, atualizar no banco de dados)
        # Aqui, apenas logamos a informação
        logger.info(f"Atualizando status do pagamento MB WAY {request_id} para {status}")
        
        # Em produção, enviar email de confirmação ao cliente
        
        return jsonify({
            "success": True,
            "message": "Callback processado com sucesso"
        }), 200
        
    except Exception as e:
        logger.exception(f"Erro ao processar callback MB WAY: {str(e)}")
        return jsonify({"error": "Erro ao processar callback MB WAY"}), 500

def process_multibanco_callback(data):
    """
    Processa callback de pagamento Multibanco
    """
    try:
        # Validar dados do callback
        required_fields = ["reference", "entity", "status"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            logger.warning(f"Campos obrigatórios em falta no callback Multibanco: {', '.join(missing_fields)}")
            return jsonify({
                "error": f"Campos obrigatórios em falta: {', '.join(missing_fields)}"
            }), 400
            
        reference = data.get("reference")
        entity = data.get("entity")
        status = data.get("status")
        
        # Atualizar status do pagamento (em produção, atualizar no banco de dados)
        # Aqui, apenas logamos a informação
        logger.info(f"Atualizando status do pagamento Multibanco {entity}/{reference} para {status}")
        
        # Em produção, enviar email de confirmação ao cliente
        
        return jsonify({
            "success": True,
            "message": "Callback processado com sucesso"
        }), 200
        
    except Exception as e:
        logger.exception(f"Erro ao processar callback Multibanco: {str(e)}")
        return jsonify({"error": "Erro ao processar callback Multibanco"}), 500

def process_payshop_callback(data):
    """
    Processa callback de pagamento Payshop
    """
    try:
        # Validar dados do callback
        required_fields = ["reference", "status"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            logger.warning(f"Campos obrigatórios em falta no callback Payshop: {', '.join(missing_fields)}")
            return jsonify({
                "error": f"Campos obrigatórios em falta: {', '.join(missing_fields)}"
            }), 400
            
        reference = data.get("reference")
        status = data.get("status")
        
        # Atualizar status do pagamento (em produção, atualizar no banco de dados)
        # Aqui, apenas logamos a informação
        logger.info(f"Atualizando status do pagamento Payshop {reference} para {status}")
        
        # Em produção, enviar email de confirmação ao cliente
        
        return jsonify({
            "success": True,
            "message": "Callback processado com sucesso"
        }), 200
        
    except Exception as e:
        logger.exception(f"Erro ao processar callback Payshop: {str(e)}")
        return jsonify({"error": "Erro ao processar callback Payshop"}), 500

@payment_bp.route("/status/<order_id>", methods=["GET", "OPTIONS"])
@cross_origin()
def payment_status(order_id):
    """
    Endpoint para verificar o status de um pagamento
    """
    # Tratar pedidos OPTIONS para CORS
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200
        
    try:
        # Em produção, buscar status do pagamento no banco de dados
        # Aqui, apenas retornamos um status fictício
        logger.info(f"Verificando status do pagamento {order_id}")
        
        # Simular busca de dados
        payment_data = {
            "orderId": order_id,
            "status": "pending",  # Em produção, buscar status real
            "method": "mbway",
            "amount": 30.0,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return jsonify({
            "success": True,
            "orderId": order_id,
            "status": payment_data.get("status"),
            "method": payment_data.get("method"),
            "amount": payment_data.get("amount"),
            "date": payment_data.get("date")
        }), 200
        
    except Exception as e:
        logger.exception(f"Erro ao verificar status do pagamento: {str(e)}")
        return jsonify({"error": "Erro ao verificar status do pagamento", "success": False}), 500

def save_payment_data(order_id, method, amount, data):
    """
    Salva dados do pagamento
    Em produção, salvar em banco de dados
    """
    # Aqui, apenas logamos a informação
    logger.info(f"Salvando dados do pagamento {order_id} ({method}, {amount}€)")
    logger.info(f"Dados: {json.dumps(data, indent=2)}")
    
    # Em produção, salvar em banco de dados
    # Exemplo: db.payments.insert_one(data)
    
    return True
