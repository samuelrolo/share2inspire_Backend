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

# Armazenamento temporário
payment_data_store = {}

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

def send_confirmation_email(email, name, payment_result):
    """Envia email de confirmação"""
    if not email or not BREVO_API_KEY:
        return False
    
    try:
        method = payment_result.get('method', 'unknown')
        
        if method == 'multibanco':
            subject = "Referência Multibanco - Share2Inspire"
            content = f"""
            <h2>Pagamento Multibanco</h2>
            <p>Olá {name},</p>
            <p>Aqui estão os dados para pagamento:</p>
            <ul>
                <li><strong>Entidade:</strong> {payment_result.get('entity')}</li>
                <li><strong>Referência:</strong> {payment_result.get('reference')}</li>
                <li><strong>Valor:</strong> €{payment_result.get('amount')}</li>
                <li><strong>Validade:</strong> {payment_result.get('expiryDate')}</li>
            </ul>
            """
        elif method == 'mbway':
            subject = "Pagamento MB WAY - Share2Inspire"
            content = f"""
            <h2>Pagamento MB WAY</h2>
            <p>Olá {name},</p>
            <p>O seu pagamento MB WAY foi iniciado.</p>
            <p><strong>Valor:</strong> €{payment_result.get('amount')}</p>
            <p>Verifique a sua app MB WAY para confirmar o pagamento.</p>
            """
        else:
            subject = "Pagamento Payshop - Share2Inspire"
            content = f"""
            <h2>Pagamento Payshop</h2>
            <p>Olá {name},</p>
            <p>Aqui estão os dados para pagamento:</p>
            <ul>
                <li><strong>Referência:</strong> {payment_result.get('reference')}</li>
                <li><strong>Valor:</strong> €{payment_result.get('amount')}</li>
                <li><strong>Validade:</strong> {payment_result.get('expiryDate')}</li>
            </ul>
            """
        
        # Enviar via Brevo
        brevo_data = {
            "sender": {
                "name": BREVO_SENDER_NAME,
                "email": BREVO_SENDER_EMAIL
            },
            "to": [{"email": email, "name": name}],
            "subject": subject,
            "htmlContent": content
        }
        
        headers = {
            'accept': 'application/json',
            'api-key': BREVO_API_KEY,
            'content-type': 'application/json'
        }
        
        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            json=brevo_data,
            headers=headers
        )
        
        return response.status_code == 201
        
    except Exception as e:
        logger.error(f"Erro ao enviar email: {str(e)}")
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
                payment_result
            )
            payment_result['emailSent'] = email_sent
        
        # Guardar dados para callback
        order_id = normalized_data.get('orderId')
        payment_data_store[order_id] = {
            'data': normalized_data,
            'result': payment_result,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
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
    """Callback para notificações de pagamento"""
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        logger.info("Callback recebido")
        logger.info(f"Method: {request.method}")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Args: {dict(request.args)}")
        logger.info(f"Form: {dict(request.form)}")
        
        # Processar callback conforme necessário
        return jsonify({'success': True, 'message': 'Callback processado'})
        
    except Exception as e:
        logger.error(f"Erro no callback: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@payment_bp.route('/status/<order_id>', methods=['GET', 'OPTIONS'])
def check_payment_status(order_id):
    """Verifica status de pagamento"""
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        if order_id in payment_data_store:
            return jsonify(payment_data_store[order_id])
        else:
            return jsonify({
                'success': False,
                'error': 'Pagamento não encontrado'
            }), 404
            
    except Exception as e:
        logger.error(f"Erro ao verificar status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
            
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
            send_confirmation_email(normalized_data.get('email'), normalized_data.get('name'), result)
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
            send_confirmation_email(normalized_data.get('email'), normalized_data.get('name'), result)
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
            send_confirmation_email(normalized_data.get('email'), normalized_data.get('name'), result)
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


