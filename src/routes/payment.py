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
            
            return jsonify({
                "success": True,
                "method": "mbway",
                "reference": result.get("RequestId"),
                "amount": amount,
                "orderId": order_id,
                "phone": phone,
                "status": result.get("Status")
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
        # Preparar dados para API Ifthenpay (atualizado para a nova API)
        payload = {
            "payshopKey": IFTHENPAY_PAYSHOP_KEY,
            "id": order_id,
            "valor": amount,
            "validade": data.get("validDays", "")  # Formato YYYYMMDD ou vazio
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
                "validity": result.get("ExpiryDate", ""),
                "status": "pending"
            }
            save_payment_data(order_id, "payshop", amount, payment_data)
            
            return jsonify({
                "success": True,
                "method": "payshop",
                "reference": result.get("Reference"),
                "amount": amount,
                "orderId": order_id,
                "validity": result.get("ExpiryDate", "")
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

@payment_bp.route("/callback", methods=["POST", "OPTIONS"])
@cross_origin()
def payment_callback():
    """
    Endpoint para receber callbacks de pagamento da Ifthenpay
    """
    # Tratar pedidos OPTIONS para CORS
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200
        
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
        reference = data.get("reference") or data.get("referenceId") or data.get("RequestId")
        amount = data.get("amount") or data.get("Amount")
        status = data.get("status", "unknown").lower()
        
        # Validar dados mínimos
        if not all([order_id, reference, amount]):
            logger.warning("Dados de callback incompletos")
            return jsonify({"error": "Dados de callback incompletos"}), 400
        
        # Processar pagamento com base no status
        if status == "paid" or status == "completed" or status == "000":
            # Atualizar status do pagamento
            update_payment_status(order_id, "paid")
            
            # Enviar email de confirmação ao cliente
            send_payment_confirmation_email(order_id)
            
            logger.info(f"Pagamento {payment_method} confirmado para pedido {order_id}")
            return jsonify({"success": True, "message": "Pagamento processado com sucesso"}), 200
        else:
            logger.warning(f"Status de pagamento não reconhecido: {status}")
            return jsonify({"success": False, "message": f"Status não processado: {status}"}), 200
            
    except Exception as e:
        logger.exception(f"Erro ao processar callback de pagamento: {str(e)}")
        return jsonify({"error": "Erro ao processar callback"}), 500

@payment_bp.route("/status/<order_id>", methods=["GET", "OPTIONS"])
@cross_origin()
def payment_status(order_id):
    """
    Verifica o status de um pagamento
    """
    # Tratar pedidos OPTIONS para CORS
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200
        
    try:
        # Obter dados do pagamento
        payment = get_payment_by_order_id(order_id)
        
        if not payment:
            return jsonify({
                "success": False,
                "error": "Pagamento não encontrado"
            }), 404
        
        return jsonify({
            "success": True,
            "payment": payment
        }), 200
            
    except Exception as e:
        logger.exception(f"Erro ao consultar status do pagamento: {str(e)}")
        return jsonify({"error": "Erro ao consultar status do pagamento", "success": False}), 500

# Implementação de armazenamento temporário em memória (substituir por banco de dados em produção)
payment_storage = {}

def save_payment_data(order_id, method, amount, data):
    """
    Salva dados do pagamento
    Em produção, substituir por armazenamento em banco de dados
    """
    logger.info(f"Salvando dados de pagamento para pedido {order_id}")
    payment_storage[order_id] = data

def update_payment_status(order_id, status):
    """
    Atualiza status do pagamento
    Em produção, substituir por atualização em banco de dados
    """
    logger.info(f"Atualizando status do pagamento para pedido {order_id}: {status}")
    if order_id in payment_storage:
        payment_storage[order_id]["status"] = status
        return True
    return False

def get_payment_by_order_id(order_id):
    """
    Obtém dados do pagamento pelo ID do pedido
    Em produção, substituir por consulta em banco de dados
    """
    return payment_storage.get(order_id)

def send_payment_confirmation_email(order_id):
    """
    Envia email de confirmação de pagamento usando a API Brevo
    """
    try:
        # Obter dados do pagamento
        payment_data = get_payment_by_order_id(order_id)
        
        if not payment_data:
            logger.warning(f"Dados de pagamento não encontrados para pedido {order_id}")
            return False
            
        # Verificar se há email do cliente
        customer_email = payment_data.get("customerEmail")
        if not customer_email:
            logger.warning(f"Email do cliente não encontrado para pedido {order_id}")
            return False
            
        # Configurar email usando Brevo
        url = "https://api.brevo.com/v3/smtp/email"
        
        headers = {
            "accept": "application/json",
            "api-key": BREVO_API_KEY,
            "content-type": "application/json"
        }
        
        # Formatar data de pagamento
        payment_date = payment_data.get("date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Formatar data e hora da marcação
        appointment_date = payment_data.get("appointmentDate", "")
        appointment_time = payment_data.get("appointmentTime", "")
        
        # Formatar data da marcação para exibição
        formatted_appointment_date = ""
        if appointment_date:
            try:
                date_obj = datetime.strptime(appointment_date, "%Y-%m-%d")
                formatted_appointment_date = date_obj.strftime("%d/%m/%Y")
            except:
                formatted_appointment_date = appointment_date
        
        # Determinar método de pagamento em português
        payment_method_pt = {
            "multibanco": "Multibanco",
            "mbway": "MB WAY",
            "payshop": "Payshop"
        }.get(payment_data.get("method", ""), "Desconhecido")
        
        # Dados do email
        payload = {
            "sender": {
                "name": BREVO_SENDER_NAME,
                "email": BREVO_SENDER_EMAIL
            },
            "to": [
                {
                    "email": customer_email,
                    "name": payment_data.get("customerName", "Cliente")
                }
            ],
            "subject": "Confirmação de Pagamento - Share2Inspire",
            "htmlContent": f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background-color: #4CAF50; color: white; padding: 10px; text-align: center; }}
                        .content {{ padding: 20px; background-color: #f9f9f9; }}
                        .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #777; }}
                        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                        th {{ background-color: #f2f2f2; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>Confirmação de Pagamento</h2>
                        </div>
                        <div class="content">
                            <p>Caro(a) {payment_data.get('customerName', 'Cliente')},</p>
                            
                            <p>O seu pagamento foi processado com <strong>sucesso</strong>!</p>
                            
                            <h3>Detalhes da Marcação:</h3>
                            <table>
                                <tr>
                                    <th>Serviço:</th>
                                    <td>{payment_data.get('description', 'Serviço Share2Inspire')}</td>
                                </tr>
                                <tr>
                                    <th>Valor:</th>
                                    <td>{payment_data.get('amount', 0)}€</td>
                                </tr>
                                <tr>
                                    <th>Data do Pagamento:</th>
                                    <td>{payment_date}</td>
                                </tr>
                                <tr>
                                    <th>Método de Pagamento:</th>
                                    <td>{payment_method_pt}</td>
                                </tr>
                                <tr>
                                    <th>Referência:</th>
                                    <td>{payment_data.get('reference', 'N/A')}</td>
                                </tr>
                                {"<tr><th>Data da Marcação:</th><td>" + formatted_appointment_date + "</td></tr>" if formatted_appointment_date else ""}
                                {"<tr><th>Hora da Marcação:</th><td>" + appointment_time + "</td></tr>" if appointment_time else ""}
                            </table>
                            
                            <p>Obrigado por escolher a Share2Inspire. Estamos ansiosos para o servir!</p>
                            
                            <p>Se tiver alguma dúvida, não hesite em contactar-nos.</p>
                            
                            <p>Com os melhores cumprimentos,<br>
                            Equipa Share2Inspire</p>
                        </div>
                        <div class="footer">
                            <p>© 2025 Share2Inspire. Todos os direitos reservados.</p>
                            <p>Este é um email automático, por favor não responda.</p>
                        </div>
                    </div>
                </body>
                </html>
            """
        }
        
        # Enviar email
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 201:
            logger.info(f"Email de confirmação enviado com sucesso para pedido {order_id}")
            return True
        else:
            logger.error(f"Erro ao enviar email de confirmação: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.exception(f"Erro ao enviar email de confirmação: {str(e)}")
        return False
