#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de processamento de pagamentos CORRIGIDO para Share2Inspire
Versão atualizada com endpoints oficiais IfthenPay 2024
Baseado na documentação oficial: https://www.ifthenpay.com/docs/
"""

import os
import json
import logging
import datetime
import requests
import traceback
import urllib.parse
from flask import Blueprint, request, jsonify, Response
from dotenv import load_dotenv
from utils.secrets import get_secret
from utils.datastore_client import get_datastore_client
from utils.email import (
    send_email_with_attachments,
    get_email_template_1,
    get_email_template_2,
    get_email_template_3,
    get_email_template_4
)

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Criar blueprint
payment_bp = Blueprint('payment', __name__)

# Configurações da IfthenPay - ENDPOINTS OFICIAIS 2024
IFTHENPAY_MULTIBANCO_URL = "https://api.ifthenpay.com/multibanco/reference/init"
IFTHENPAY_MBWAY_URL = "https://api.ifthenpay.com/spg/payment/mbway"
IFTHENPAY_PAYSHOP_URL = "https://api.ifthenpay.com/payshop/reference/init"

# Chaves da IfthenPay
IFTHENPAY_MBWAY_KEY = get_secret('IFTHENPAY_MBWAY_KEY')
IFTHENPAY_MULTIBANCO_KEY = get_secret('IFTHENPAY_MULTIBANCO_KEY')
IFTHENPAY_PAYSHOP_KEY = get_secret('IFTHENPAY_PAYSHOP_KEY')

# Configurações do Brevo
BREVO_API_KEY = get_secret('BREVO_API_KEY')
BREVO_SENDER_NAME = os.getenv('BREVO_SENDER_NAME', 'Share2Inspire')
BREVO_SENDER_EMAIL = os.getenv('BREVO_SENDER_EMAIL', 'noreply@share2inspire.pt')

# URL do Google Apps Script
GOOGLE_APPS_SCRIPT_URL = os.getenv('GOOGLE_APPS_SCRIPT_URL', '')

# Anti-phishing key for webhook validation
IFTHENPAY_ANTIPHISHING_KEY = get_secret('IFTHENPAY_ANTIPHISHING_KEY', default='dev-key-placeholder')

# Datastore client for persistent storage
datastore_client = get_datastore_client()

def handle_cors_preflight():
    """Tratamento de CORS"""
    response = jsonify({"success": True})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response, 200

def format_phone_number(phone):
    """Formata número de telefone para padrão português"""
    if not phone:
        return None
    
    # Remove caracteres não numéricos
    phone = ''.join(filter(str.isdigit, str(phone)))
    
    # Se já tem 351, mantém
    if phone.startswith('351'):
        return phone
    
    # Se começa com 9 e tem 9 dígitos, adiciona 351
    if phone.startswith('9') and len(phone) == 9:
        return '351' + phone
    
    return phone

def normalize_payment_data(data):
    """Normaliza dados de pagamento"""
    normalized = {}
    
    # Mapeamento de campos
    field_map = {
        'name': ['name', 'nome', 'customerName', 'customer_name'],
        'email': ['email', 'customerEmail', 'customer_email'],
        'phone': ['phone', 'telefone', 'customerPhone', 'customer_phone', 'mobileNumber', 'mobile_number'],
        'amount': ['amount', 'valor', 'price'],
        'orderId': ['orderId', 'order_id', 'id'],
        'paymentMethod': ['paymentMethod', 'payment_method', 'method'],
        'description': ['description', 'descricao', 'service']
    }
    
    # Normalizar campos
    for standard_field, possible_names in field_map.items():
        for field_name in possible_names:
            if field_name in data and data[field_name]:
                normalized[standard_field] = data[field_name]
                break
    
    # Garantir campos obrigatórios
    if 'orderId' not in normalized:
        normalized['orderId'] = f"ORDER-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    if 'amount' not in normalized:
        normalized['amount'] = "30.00"
    
    # Formatar telefone
    if 'phone' in normalized:
        normalized['phone'] = format_phone_number(normalized['phone'])
    
    return normalized

def create_multibanco_payment(data):
    """Cria pagamento Multibanco usando API oficial"""
    try:
        # Preparar dados conforme documentação oficial
        payload = {
            "mbKey": IFTHENPAY_MULTIBANCO_KEY,
            "orderId": data.get('orderId'),
            "amount": str(data.get('amount', '30.00')),
            "description": data.get('description', 'Pagamento Share2Inspire'),
            "url": "https://share2inspire.pt/callback",
            "clientCode": "123",
            "clientName": data.get('name', ''),
            "clientEmail": data.get('email', ''),
            "clientUsername": data.get('name', '').replace(' ', '').lower(),
            "clientPhone": data.get('phone', ''),
            "expiryDays": "3"
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        logger.info(f"Enviando request Multibanco: {IFTHENPAY_MULTIBANCO_URL}")
        logger.info(f"Payload: {payload}")
        
        response = requests.post(
            IFTHENPAY_MULTIBANCO_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        logger.info(f"Resposta Multibanco - Status: {response.status_code}")
        logger.info(f"Resposta Multibanco - Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'method': 'multibanco',
                'entity': result.get('Entity'),
                'reference': result.get('Reference'),
                'amount': result.get('Amount'),
                'orderId': result.get('OrderId'),
                'expiryDate': result.get('ExpiryDate'),
                'requestId': result.get('RequestId')
            }
        else:
            return {
                'success': False,
                'error': f"Erro na API Multibanco: {response.status_code} - {response.text}"
            }
            
    except Exception as e:
        logger.error(f"Erro ao criar pagamento Multibanco: {str(e)}")
        return {
            'success': False,
            'error': f"Erro interno: {str(e)}"
        }

def create_mbway_payment(data):
    """Cria pagamento MB WAY usando API oficial"""
    try:
        # Preparar dados conforme documentação oficial
        payload = {
            "mbWayKey": IFTHENPAY_MBWAY_KEY,
            "orderId": data.get('orderId'),
            "amount": str(data.get('amount', '30.00')),
            "mobileNumber": data.get('phone', ''),
            "email": data.get('email', ''),
            "description": data.get('description', 'Pagamento Share2Inspire')
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        logger.info(f"Enviando request MB WAY: {IFTHENPAY_MBWAY_URL}")
        logger.info(f"Payload: {payload}")
        
        response = requests.post(
            IFTHENPAY_MBWAY_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        logger.info(f"Resposta MB WAY - Status: {response.status_code}")
        logger.info(f"Resposta MB WAY - Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'method': 'mbway',
                'amount': result.get('Amount'),
                'orderId': result.get('OrderId'),
                'message': result.get('Message'),
                'requestId': result.get('RequestId'),
                'status': result.get('Status')
            }
        else:
            return {
                'success': False,
                'error': f"Erro na API MB WAY: {response.status_code} - {response.text}"
            }
            
    except Exception as e:
        logger.error(f"Erro ao criar pagamento MB WAY: {str(e)}")
        return {
            'success': False,
            'error': f"Erro interno: {str(e)}"
        }

def check_mbway_payment_status(request_id, mb_way_key=None):
    """
    Verifica o status de um pagamento MB WAY via API Ifthenpay.
    IMPORTANTE: A API Ifthenpay usa requestId (não orderId) para verificar status!
    
    Args:
        request_id: RequestId retornado pela API quando o pagamento foi iniciado
        mb_way_key: Chave MB WAY (opcional, usa global se não fornecido)
        
    Returns:
        dict com status do pagamento
    """
    try:
        if not mb_way_key:
            mb_way_key = IFTHENPAY_MBWAY_KEY
        
        # Endpoint de verificação de status da Ifthenpay
        # CORRIGIDO: Usar requestId conforme documentação oficial
        status_url = "https://api.ifthenpay.com/spg/payment/mbway/status"
        
        params = {
            "mbWayKey": mb_way_key,
            "requestId": request_id  # CORRIGIDO: era orderId, agora é requestId
        }
        
        logger.info(f"[STATUS CHECK] Verificando pagamento com requestId: {request_id}")
        
        response = requests.get(
            status_url,
            params=params,
            timeout=15
        )
        
        logger.info(f"[STATUS CHECK] Response - Status: {response.status_code}")
        logger.info(f"[STATUS CHECK] Response - Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Mapear status da Ifthenpay
            # Conforme documentação: "000" = Pending, outros valores indicam conclusão
            status_code = result.get('Status', '')
            message = result.get('Message', '')
            
            # Status codes conforme documentação Ifthenpay:
            # "000" = Pending (aguardando confirmação do utilizador)
            # Qualquer outro código com Message "Success" = Pago
            # "REJECTED" ou similar = Rejeitado
            
            is_paid = (status_code != '000' and message.lower() == 'success') or status_code in ['PAGO', 'SUCCESS', '1']
            is_pending = status_code == '000'
            
            logger.info(f"[STATUS CHECK] Status: {status_code}, Message: {message}, isPaid: {is_paid}, isPending: {is_pending}")
            
            return {
                'success': True,
                'requestId': request_id,
                'status': status_code,
                'isPaid': is_paid,
                'isPending': is_pending,
                'amount': result.get('Amount'),
                'message': message,
                'rawResponse': result
            }
        else:
            return {
                'success': False,
                'error': f"Erro ao verificar status: {response.status_code} - {response.text}"
            }
            
    except Exception as e:
        logger.error(f"[STATUS CHECK] Erro: {str(e)}")
        return {
            'success': False,
            'error': f"Erro interno: {str(e)}"
        }

def create_payshop_payment(data):
    """Cria pagamento Payshop usando API oficial"""
    try:
        # Preparar dados conforme documentação oficial
        payload = {
            "payshopKey": IFTHENPAY_PAYSHOP_KEY,
            "orderId": data.get('orderId'),
            "amount": str(data.get('amount', '30.00')),
            "description": data.get('description', 'Pagamento Share2Inspire'),
            "url": "https://share2inspire.pt/callback",
            "clientCode": "123",
            "clientName": data.get('name', ''),
            "clientEmail": data.get('email', ''),
            "clientPhone": data.get('phone', ''),
            "expiryDays": "3"
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        logger.info(f"Enviando request Payshop: {IFTHENPAY_PAYSHOP_URL}")
        logger.info(f"Payload: {payload}")
        
        response = requests.post(
            IFTHENPAY_PAYSHOP_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        logger.info(f"Resposta Payshop - Status: {response.status_code}")
        logger.info(f"Resposta Payshop - Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'method': 'payshop',
                'reference': result.get('Reference'),
                'amount': result.get('Amount'),
                'orderId': result.get('OrderId'),
                'expiryDate': result.get('ExpiryDate'),
                'requestId': result.get('RequestId')
            }
        else:
            return {
                'success': False,
                'error': f"Erro na API Payshop: {response.status_code} - {response.text}"
            }
            
    except Exception as e:
        logger.error(f"Erro ao criar pagamento Payshop: {str(e)}")
        return {
            'success': False,
            'error': f"Erro interno: {str(e)}"
        }

def send_confirmation_email(email, name, payment_result, description=""):
    """Envia email de confirmação inicial com link de pagamento (Templates 1, 2 ou 3)"""
    if not email:
        return False
    
    try:
        # Normalizar service description para matching robusto
        service = description.lower().strip()
        order_id = payment_result.get('orderId', '')
        
        logger.info(f"[EMAIL] Selecionando template para serviço: '{description}' (normalized: '{service}')")
        logger.info(f"[EMAIL] Order ID: {order_id}")
        
        # Gerar link de pagamento
        payment_link = "https://share2inspire.pt/pagamento"  # Fallback
        
        # Tentar extrair link se existir no resultado
        if payment_result.get('payment_url'):
            payment_link = payment_result.get('payment_url')
        elif payment_result.get('method') == 'multibanco':
            payment_link = f"https://share2inspire.pt/pagamento?ref={payment_result.get('reference')}"

        # Template selection com matching robusto e logging
        # CV ANALYZER - PRIORIDADE MÁXIMA (check first to avoid fallback)
        if any(keyword in service for keyword in ['analyzer', 'analyser', 'análise', 'analise']) or order_id.startswith('CVA-'):
            subject = "Relatório de Análise de CV | Pagamento para acesso completo"
            html_content = get_email_template_3(name, payment_link)
            logger.info("[EMAIL] ✓ Template 3 selecionado (CV Analyzer)")
        
        # KICKSTART PRO
        elif "kickstart" in service:
            subject = "Confirmação do pedido | Pagamento Kickstart Pro"
            html_content = get_email_template_1(name, payment_link)
            logger.info("[EMAIL] ✓ Template 1 selecionado (Kickstart Pro)")
        
        # CV REVIEW / REVISÃO PROFISSIONAL
        elif "revisão" in service or "revisao" in service or "cv review" in service or "cv professional" in service:
            subject = "Confirmação do pedido | Pagamento Revisão Profissional de CV"
            html_content = get_email_template_2(name, payment_link)
            logger.info("[EMAIL] ✓ Template 2 selecionado (CV Review)")
        
        # FALLBACK
        else:
            subject = "Confirmação de Pedido | Share2Inspire"
            html_content = get_email_template_1(name, payment_link)
            logger.warning(f"[EMAIL] ⚠ Fallback Template 1 usado para serviço desconhecido: '{description}'")

        logger.info(f"[EMAIL] Enviando para: {email} com subject: {subject}")
        success, msg = send_email_with_attachments(email, name, subject, html_content)
        
        if success:
            logger.info(f"[EMAIL] ✓ Email enviado com sucesso para {email}")
        else:
            logger.error(f"[EMAIL] ✗ Falha ao enviar email: {msg}")
        
        return success
        
    except Exception as e:
        logger.error(f"[EMAIL] ✗ Erro ao enviar email de pagamento: {str(e)}")
        logger.error(traceback.format_exc())
        return False

@payment_bp.route('/initiate', methods=['POST', 'OPTIONS'])
def initiate_payment():
    """Endpoint principal para iniciar pagamentos"""
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        # Obter dados do request
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        logger.info(f"Dados recebidos: {data}")
        
        # Normalizar dados
        normalized_data = normalize_payment_data(data)
        
        logger.info(f"Dados normalizados: {normalized_data}")
        
        # Determinar método de pagamento
        payment_method = normalized_data.get('paymentMethod', 'mbway').lower()
        
        # Criar pagamento conforme método
        if payment_method in ['mb', 'multibanco']:
            payment_result = create_multibanco_payment(normalized_data)
        elif payment_method in ['mbway', 'mb_way']:
            payment_result = create_mbway_payment(normalized_data)
        elif payment_method in ['payshop']:
            payment_result = create_payshop_payment(normalized_data)
        else:
            return jsonify({
                'success': False,
                'error': f'Método de pagamento não suportado: {payment_method}'
            }), 400
        
        # Se pagamento foi criado com sucesso, enviar email
        if payment_result.get('success'):
            email_sent = send_confirmation_email(
                normalized_data.get('email'),
                normalized_data.get('name'),
                payment_result,
                normalized_data.get('description', '')
            )
            payment_result['emailSent'] = email_sent
        
        # Guardar dados para callback usando Datastore
        order_id = normalized_data.get('orderId')
        datastore_client.save_payment_record(
            order_id=order_id,
            payment_data=payment_result,
            user_data=normalized_data
        )
        
        return jsonify(payment_result)
        
    except Exception as e:
        logger.error(f"Erro ao processar pagamento: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@payment_bp.route('/callback', methods=['POST', 'GET', 'OPTIONS'])
def payment_callback():
    """
    DEPRECATED: Generic callback endpoint. Use /webhook-mbway instead.
    Kept for backwards compatibility.
    """
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    logger.warning("Legacy /callback endpoint called. Consider using /webhook-mbway.")
    return webhook_mbway()


@payment_bp.route('/webhook-mbway', methods=['POST', 'GET', 'OPTIONS'])
def webhook_mbway():
    """
    Webhook dedicado para callbacks MB WAY da Ifthenpay.
    Valida pagamento confirmado e dispara entrega automática de relatórios.
    
    Parâmetros esperados (GET query params ou POST form):
    - chave: Anti-phishing key
    - referencia: Order ID
    - valor: Amount paid
    - estado: Payment status ('PAGO' for success)
    - data: Payment timestamp (dd-MM-yyyy HH:mm:ss)
    """
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        # Obter parâmetros (Ifthenpay envia via GET para MB WAY)
        params = request.args.to_dict()
        if not params:
            params = request.get_json() if request.is_json else request.form.to_dict()
        
        logger.info(f"[WEBHOOK MB WAY] Recebido: {params}")
        
        # 1. Validar Anti-Phishing Key
        received_key = params.get('chave') or params.get('key')
        if not received_key or received_key != IFTHENPAY_ANTIPHISHING_KEY:
            logger.warning(f"[WEBHOOK MB WAY] Anti-phishing key inválida: {received_key}")
            return Response("Invalid key", status=403)
        
        # 2. Extrair dados
        order_id = params.get('referencia') or params.get('orderId') or params.get('id_pedido')
        amount = params.get('valor') or params.get('amount')
        status = params.get('estado') or params.get('status')
        payment_date = params.get('data') or params.get('date')
        
        if not order_id:
            logger.error("[WEBHOOK MB WAY] Order ID não fornecido")
            return Response("Missing order ID", status=400)
        
        logger.info(f"[WEBHOOK MB WAY] OrderID: {order_id}, Amount: {amount}, Status: {status}")
        
        # 3. Validar status de pagamento
        if status and status.upper() != 'PAGO':
            logger.warning(f"[WEBHOOK MB WAY] Status não confirmado: {status}")
            return Response("Payment not confirmed", status=200)  # Return 200 to stop retries
        
        # 4. Recuperar record do Datastore
        record = datastore_client.get_payment_record(order_id)
        
        if not record:
            logger.error(f"[WEBHOOK MB WAY] Record não encontrado: {order_id}")
            return Response("Order not found", status=404)
        
        # 5. Verificar se já foi entregue (evitar duplicados)
        if record.get('delivered'):
            logger.info(f"[WEBHOOK MB WAY] Relatório já entregue para: {order_id}")
            return Response("Already delivered", status=200)
        
        # 6. Atualizar record com dados de confirmação
        datastore_client.update_record(order_id, {
            'payment_confirmed_at': payment_date or datetime.datetime.now().isoformat(),
            'payment_amount_confirmed': amount,
            'payment_status': status
        })
        
        # 7. Enviar Email 4 (Confirmação de Pagamento)
        user_data = record.get('user_data', {})
        if user_data.get('email'):
            confirm_html = get_email_template_4(user_data.get('name', 'Cliente'))
            send_email_with_attachments(
                user_data.get('email'),
                user_data.get('name', 'Cliente'),
                "Pagamento confirmado | Próximos passos",
                confirm_html
            )
        
        # 8. Trigger automático de entrega se for CV Analyzer
        description = user_data.get('description', '').lower()
        if 'analyzer' in description or order_id.startswith('CVA-'):
            logger.info(f"[WEBHOOK MB WAY] Disparando entrega automática para: {order_id}")
            
            # Tentar entregar relatório automaticamente
            analysis_data = record.get('analysis_data')
            if analysis_data:
                try:
                    # Import here to avoid circular dependency
                    from routes.services import deliver_report_internal
                    
                    delivery_result = deliver_report_internal(
                        order_id=order_id,
                        analysis_data=analysis_data,
                        user_data=user_data
                    )
                    
                    if delivery_result.get('success'):
                        logger.info(f"[WEBHOOK MB WAY] Relatório entregue com sucesso: {order_id}")
                    else:
                        logger.error(f"[WEBHOOK MB WAY] Erro ao entregar: {delivery_result.get('error')}")
                        
                except Exception as e:
                    logger.error(f"[WEBHOOK MB WAY] Exceção ao entregar relatório: {e}")
                    logger.error(traceback.format_exc())
            else:
                logger.warning(f"[WEBHOOK MB WAY] Sem dados de análise para: {order_id}")
        
        logger.info(f"[WEBHOOK MB WAY] Processamento concluído: {order_id}")
        
        # CRITICAL: Always return HTTP 200 to Ifthenpay to stop retries
        return Response("OK", status=200)
        
    except Exception as e:
        logger.error(f"[WEBHOOK MB WAY] Erro: {str(e)}")
        logger.error(traceback.format_exc())
        # Still return 200 to avoid infinite retries
        return Response("Error processed", status=200)

def deliver_report_for_order(order_id, record):
    """
    Função helper para entregar relatório quando pagamento é confirmado.
    """
    try:
        analysis_data = record.get('analysis_data')
        user_data = record.get('user_data')
        
        if not analysis_data or not user_data:
            logger.error(f"[DELIVER] Dados incompletos para orderId: {order_id}")
            return {'success': False, 'error': 'Dados incompletos'}
        
        # Import aqui para evitar circular dependency
        from routes.services import deliver_report_internal
        
        result = deliver_report_internal(
            order_id=order_id,
            analysis_data=analysis_data,
            user_data=user_data
        )
        
        if result.get('success'):
            datastore_client.mark_as_delivered(order_id)
            logger.info(f"[DELIVER] Relatório entregue com sucesso para orderId: {order_id}")
        else:
            logger.error(f"[DELIVER] Erro ao entregar relatório: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"[DELIVER] Erro: {str(e)}")
        return {'success': False, 'error': str(e)}


@payment_bp.route('/status/<order_id>', methods=['GET', 'OPTIONS'])
def check_payment_status(order_id):
    """
    Verifica status de pagamento via API Ifthenpay e Datastore.
    CORRIGIDO: Agora usa requestId (não orderId) para verificar na API Ifthenpay.
    """
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        logger.info(f"[STATUS] Verificando pagamento para orderId: {order_id}")
        
        # Primeiro verificar no Datastore local
        record = datastore_client.get_payment_record(order_id)
        
        if record and record.get('paid'):
            logger.info(f"[STATUS] Pagamento encontrado no Datastore como PAGO")
            response = jsonify({
                'success': True,
                'paid': True,
                'status': 'PAID',
                'record': record
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        # Obter requestId do record (guardado quando o pagamento foi iniciado)
        request_id = None
        if record:
            payment_data = record.get('payment_data', {})
            request_id = payment_data.get('requestId')
            logger.info(f"[STATUS] RequestId encontrado no Datastore: {request_id}")
        
        if not request_id:
            logger.warning(f"[STATUS] RequestId não encontrado para orderId: {order_id}")
            response = jsonify({
                'success': True,
                'paid': False,
                'pending': True,
                'status': 'PENDING',
                'message': 'RequestId não encontrado. Aguardando confirmação via webhook.'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        # Verificar na API Ifthenpay usando requestId (NÃO orderId!)
        logger.info(f"[STATUS] Verificando na API Ifthenpay com requestId: {request_id}")
        ifthenpay_status = check_mbway_payment_status(request_id)
        
        if ifthenpay_status.get('success'):
            is_paid = ifthenpay_status.get('isPaid', False)
            is_pending = ifthenpay_status.get('isPending', True)
            
            logger.info(f"[STATUS] Ifthenpay - isPaid: {is_paid}, isPending: {is_pending}, status: {ifthenpay_status.get('status')}")
            
            # Se está pago na Ifthenpay, atualizar Datastore e entregar relatório
            if is_paid:
                datastore_client.update_payment_status(order_id, 'PAID', paid=True)
                logger.info(f"[STATUS] Pagamento confirmado como PAGO para orderId: {order_id}")
                
                # Disparar entrega do relatório
                try:
                    deliver_report_for_order(order_id, record)
                except Exception as delivery_error:
                    logger.error(f"[STATUS] Erro ao entregar relatório: {str(delivery_error)}")
            
            response = jsonify({
                'success': True,
                'paid': is_paid,
                'pending': is_pending,
                'status': 'PAID' if is_paid else ('PENDING' if is_pending else 'UNKNOWN'),
                'ifthenpayStatus': ifthenpay_status.get('status'),
                'message': ifthenpay_status.get('message', '')
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        else:
            # Erro ao verificar na Ifthenpay, retornar status pendente
            logger.warning(f"[STATUS] Erro ao verificar na Ifthenpay: {ifthenpay_status.get('error')}")
            response = jsonify({
                'success': True,
                'paid': False,
                'pending': True,
                'status': 'PENDING',
                'message': 'Aguardando confirmação'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
    except Exception as e:
        logger.error(f"[STATUS] Erro ao verificar status: {str(e)}")
        logger.error(traceback.format_exc())
        response = jsonify({'success': False, 'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@payment_bp.route('/check-payment-status', methods=['GET', 'POST', 'OPTIONS'])
def check_payment_status_and_deliver():
    """
    TEMPORARY ENDPOINT: Verifica status do pagamento via API Ifthenpay e entrega relatório se pago.
    CORRIGIDO: Agora usa requestId (não orderId) para verificar na API Ifthenpay.
    
    Query params:
        orderId: ID do pedido (requerido)
    """
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        # Obter orderId
        order_id = request.args.get('orderId') or request.json.get('orderId') if request.is_json else None
        
        if not order_id:
            return jsonify({
                'success': False,
                'error': 'orderId é obrigatório'
            }), 400
        
        logger.info(f"[MANUAL CHECK] Verificação manual solicitada para orderId: {order_id}")
        
        # 1. Verificar se já foi entregue
        if datastore_client.is_delivered(order_id):
            return jsonify({
                'success': True,
                'alreadyDelivered': True,
                'message': 'Relatório já foi entregue anteriormente'
            }), 200
        
        # 2. Recuperar dados do Datastore para obter requestId
        record = datastore_client.get_payment_record(order_id)
        
        if not record:
            return jsonify({
                'success': False,
                'error': 'Dados do pedido não encontrados'
            }), 404
        
        # Obter requestId do payment_data (guardado quando o pagamento foi iniciado)
        payment_data = record.get('payment_data', {})
        request_id = payment_data.get('requestId')
        
        if not request_id:
            logger.warning(f"[MANUAL CHECK] RequestId não encontrado para orderId: {order_id}")
            return jsonify({
                'success': True,
                'paid': False,
                'pending': True,
                'message': 'RequestId não encontrado. Aguardando confirmação via webhook.'
            }), 200
        
        logger.info(f"[MANUAL CHECK] Verificando status com requestId: {request_id}")
        
        # 3. Verificar status na Ifthenpay usando requestId (NÃO orderId!)
        status_result = check_mbway_payment_status(request_id)
        
        if not status_result.get('success'):
            return jsonify({
                'success': False,
                'error': 'Erro ao verificar status do pagamento',
                'details': status_result.get('error')
            }), 500
        
        # 4. Verificar se está pago
        if status_result.get('isPaid'):
            logger.info(f"[MANUAL CHECK] Pagamento confirmado para orderId: {order_id}")
            
            # Atualizar status no Datastore
            datastore_client.update_payment_status(order_id, 'PAID', paid=True)
            
            # Entregar relatório automaticamente
            analysis_data = record.get('analysis_data')
            user_data = record.get('user_data')
            
            if not analysis_data or not user_data:
                return jsonify({
                    'success': False,
                    'error': 'Dados incompletos para entrega'
                }), 400
            
            # Import aqui para evitar circular dependency
            from routes.services import deliver_report_internal
            
            delivery_result = deliver_report_internal(
                order_id=order_id,
                analysis_data=analysis_data,
                user_data=user_data
            )
            
            if delivery_result.get('success'):
                return jsonify({
                    'success': True,
                    'paid': True,
                    'delivered': True,
                    'message': 'Pagamento confirmado! Relatório enviado para o teu email.'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'paid': True,
                    'delivered': False,
                    'error': 'Pagamento confirmado mas erro ao entregar relatório',
                    'details': delivery_result.get('error')
                }), 500
                
        elif status_result.get('isPending'):
            return jsonify({
                'success': True,
                'paid': False,
                'pending': True,
                'message': 'Pagamento ainda não confirmado. Por favor confirma no MB WAY e tenta novamente.'
            }), 200
        else:
            return jsonify({
                'success': True,
                'paid': False,
                'pending': False,
                'message': 'Pagamento não foi concluído ou expirou. Por favor cria um novo pedido.',
                'status': status_result.get('status')
            }), 200
            
    except Exception as e:
        logger.error(f"[MANUAL CHECK] Erro: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Erro interno ao verificar pagamento'
        }), 500
            
@payment_bp.route('/multibanco', methods=['POST', 'OPTIONS'])
def process_multibanco_payment():
    """Endpoint específico para Multibanco (Compatibilidade)"""
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        normalized_data = normalize_payment_data(data)
        
        # Garantir que temos amount e orderId
        if not normalized_data.get('amount') or not normalized_data.get('orderId'):
             return jsonify({"success": False, "error": "Dados obrigatórios em falta"}), 400

        result = create_multibanco_payment(normalized_data)
        
        if result['success']:
             # Enviar email se sucesso
            send_confirmation_email(
                normalized_data.get('email'), 
                normalized_data.get('name'), 
                result,
                normalized_data.get('description', '')
            )
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint Multibanco: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@payment_bp.route('/mbway', methods=['POST', 'OPTIONS'])
def process_mbway_payment():
    """Endpoint específico para MB WAY (Compatibilidade)"""
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        normalized_data = normalize_payment_data(data)
        
        if not normalized_data.get('amount') or not normalized_data.get('phone') or not normalized_data.get('orderId'):
            return jsonify({"success": False, "error": "Dados obrigatórios em falta"}), 400
            
        result = create_mbway_payment(normalized_data)
        
        if result['success']:
            # SKIP email for MB WAY - user receives push notification on phone
            # Email will be sent AFTER payment confirmation with PDF report
            # send_confirmation_email(
            #     normalized_data.get('email'), 
            #     normalized_data.get('name'), 
            #     result,
            #     normalized_data.get('description', '')
            # )
            logger.info(f"[MB WAY] Pagamento iniciado, push notification enviada para {normalized_data.get('phone')}")
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint MB WAY: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@payment_bp.route('/payshop', methods=['POST', 'OPTIONS'])
def process_payshop_payment():
    """Endpoint específico para Payshop (Compatibilidade)"""
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        normalized_data = normalize_payment_data(data)
        
        if not normalized_data.get('amount') or not normalized_data.get('orderId'):
            return jsonify({"success": False, "error": "Dados obrigatórios em falta"}), 400
            
        result = create_payshop_payment(normalized_data)
        
        if result['success']:
            send_confirmation_email(
                normalized_data.get('email'), 
                normalized_data.get('name'), 
                result,
                normalized_data.get('description', '')
            )
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint Payshop: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@payment_bp.route('/health', methods=['GET', 'OPTIONS'])
def payment_health():
    """Health check endpoint for payment service"""
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    return jsonify({
        'service': 'payment',
        'status': 'healthy',
        'version': '2.0.0',
        'timestamp': datetime.datetime.now().isoformat(),
        'endpoints': ['mbway', 'multibanco', 'payshop', 'callback', 'status']
    })

# Log das configurações
logger.info("=== SISTEMA DE PAGAMENTOS CORRIGIDO CARREGADO ===")
logger.info(f"Multibanco URL: {IFTHENPAY_MULTIBANCO_URL}")
logger.info(f"MB WAY URL: {IFTHENPAY_MBWAY_URL}")
logger.info(f"Payshop URL: {IFTHENPAY_PAYSHOP_URL}")
logger.info(f"MBWAY KEY: {'DEFINIDA' if IFTHENPAY_MBWAY_KEY else 'NÃO DEFINIDA'}")
logger.info(f"MULTIBANCO KEY: {'DEFINIDA' if IFTHENPAY_MULTIBANCO_KEY else 'NÃO DEFINIDA'}")
logger.info(f"PAYSHOP KEY: {'DEFINIDA' if IFTHENPAY_PAYSHOP_KEY else 'NÃO DEFINIDA'}")
logger.info(f"BREVO API KEY: {'DEFINIDA' if BREVO_API_KEY else 'NÃO DEFINIDA'}")


