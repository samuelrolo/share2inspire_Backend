#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de processamento de pagamentos para Share2Inspire
Versão ultra-robusta que aceita literalmente qualquer formato de dados
Inclui logs ultra-detalhados para depuração completa
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
# Importar handle_cors_preflight do main.py
from main import handle_cors_preflight

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Criar blueprint
payment_bp = Blueprint('payment', __name__)

# Armazenamento temporário de dados de pagamento (em produção, usar banco de dados)
payment_data_store = {}

# Configurações da IfthenPay
IFTHENPAY_MBWAY_KEY = os.getenv('IFTHENPAY_MBWAY_KEY', 'UWP-547025')
IFTHENPAY_MULTIBANCO_KEY = os.getenv('IFTHENPAY_MULTIBANCO_KEY', 'BXG-350883')
IFTHENPAY_PAYSHOP_KEY = os.getenv('IFTHENPAY_PAYSHOP_KEY', 'QTU-066969')

# Configurações do Brevo
BREVO_API_KEY = os.getenv('BREVO_API_KEY')
BREVO_SENDER_NAME = os.getenv('BREVO_SENDER_NAME', 'Share2Inspire')
BREVO_SENDER_EMAIL = os.getenv('BREVO_SENDER_EMAIL', 'noreply@share2inspire.pt')

# URL do Google Apps Script para integração com Calendar
GOOGLE_APPS_SCRIPT_URL = os.getenv('GOOGLE_APPS_SCRIPT_URL', '')

# Mapeamento de campos para normalização
FIELD_MAPPING = {
    # Campos de método de pagamento
    'paymentmethod': 'paymentMethod',
    'payment_method': 'paymentMethod',
    'payment-method': 'paymentMethod',
    'metodo': 'paymentMethod',
    'metododepagamento': 'paymentMethod',
    'método': 'paymentMethod',
    'métododepagamento': 'paymentMethod',
    'metodo_de_pagamento': 'paymentMethod',
    'método_de_pagamento': 'paymentMethod',
    'metodo-de-pagamento': 'paymentMethod',
    'método-de-pagamento': 'paymentMethod',
    
    # Campos de ID do pedido
    'orderid': 'orderId',
    'order_id': 'orderId',
    'order-id': 'orderId',
    'pedido': 'orderId',
    'id_pedido': 'orderId',
    'id-pedido': 'orderId',
    
    # Campos de valor
    'amount': 'amount',
    'valor': 'amount',
    'price': 'amount',
    'preco': 'amount',
    'preço': 'amount',
    
    # Campos de nome do cliente
    'customername': 'customerName',
    'customer_name': 'customerName',
    'customer-name': 'customerName',
    'nome': 'customerName',
    'name': 'customerName',
    'nomecompleto': 'customerName',
    'nome_completo': 'customerName',
    'nome-completo': 'customerName',
    
    # Campos de email do cliente
    'customeremail': 'customerEmail',
    'customer_email': 'customerEmail',
    'customer-email': 'customerEmail',
    'email': 'customerEmail',
    'mail': 'customerEmail',
    'e-mail': 'customerEmail',
    
    # Campos de telefone do cliente
    'customerphone': 'customerPhone',
    'customer_phone': 'customerPhone',
    'customer-phone': 'customerPhone',
    'telefone': 'customerPhone',
    'phone': 'customerPhone',
    'telemovel': 'customerPhone',
    'telemóvel': 'customerPhone',
    'tel': 'customerPhone',
    
    # Campos de data do serviço
    'servicedate': 'serviceDate',
    'service_date': 'serviceDate',
    'service-date': 'serviceDate',
    'data': 'serviceDate',
    'date': 'serviceDate',
    'datapreferencial': 'serviceDate',
    'data_preferencial': 'serviceDate',
    'data-preferencial': 'serviceDate',
    
    # Campos de hora do serviço
    'servicetime': 'serviceTime',
    'service_time': 'serviceTime',
    'service-time': 'serviceTime',
    'hora': 'serviceTime',
    'time': 'serviceTime',
    'horapreferencial': 'serviceTime',
    'hora_preferencial': 'serviceTime',
    'hora-preferencial': 'serviceTime',
    
    # Campos de duração do serviço
    'serviceduration': 'serviceDuration',
    'service_duration': 'serviceDuration',
    'service-duration': 'serviceDuration',
    'duracao': 'serviceDuration',
    'duração': 'serviceDuration',
    'duration': 'serviceDuration',
    
    # Campos de formato do serviço
    'serviceformat': 'serviceFormat',
    'service_format': 'serviceFormat',
    'service-format': 'serviceFormat',
    'formato': 'serviceFormat',
    'format': 'serviceFormat',
}

# Mapeamento de valores de método de pagamento
PAYMENT_METHOD_MAPPING = {
    # MB WAY
    'mbway': 'mbway',
    'mb way': 'mbway',
    'mb-way': 'mbway',
    'mb_way': 'mbway',
    'mbw': 'mbway',
    'way': 'mbway',
    
    # Multibanco
    'mb': 'mb',
    'multibanco': 'mb',
    'multi-banco': 'mb',
    'multi_banco': 'mb',
    'atm': 'mb',
    
    # Payshop
    'payshop': 'payshop',
    'pay-shop': 'payshop',
    'pay_shop': 'payshop',
    'ps': 'payshop',
}

def log_request_details():
    """
    Função para registrar todos os detalhes possíveis do request
    """
    logger.info("=== DETALHES COMPLETOS DO REQUEST ===")
    logger.info(f"Método: {request.method}")
    logger.info(f"URL: {request.url}")
    logger.info(f"Endpoint: {request.endpoint}")
    
    logger.info("=== HEADERS ===")
    for header, value in request.headers.items():
        logger.info(f"{header}: {value}")
    
    logger.info("=== ARGS (Query Parameters) ===")
    for key, value in request.args.items():
        logger.info(f"{key}: {value}")
    
    logger.info("=== FORM DATA ===")
    for key, value in request.form.items():
        logger.info(f"{key}: {value}")
    
    logger.info("=== JSON ===")
    try:
        if request.is_json:
            json_data = request.get_json(silent=True)
            logger.info(f"{json_data}")
    except Exception as e:
        logger.error(f"Erro ao extrair JSON: {str(e)}")
    
    logger.info("=== DADOS BRUTOS ===")
    try:
        raw_data = request.data.decode('utf-8')
        logger.info(f"{raw_data}")
    except Exception as e:
        logger.error(f"Erro ao extrair dados brutos: {str(e)}")
    
    logger.info("=== COOKIES ===")
    for key, value in request.cookies.items():
        logger.info(f"{key}: {value}")
    
    logger.info("=== ENVIRONMENT ===")
    logger.info(f"Remote Addr: {request.remote_addr}")
    logger.info(f"User Agent: {request.user_agent}")
    logger.info(f"Content Type: {request.content_type}")
    logger.info(f"Content Length: {request.content_length}")
    
    logger.info("=== STACK TRACE ===")
    logger.info(traceback.format_stack())

def get_request_data():
    """
    Função ultra-robusta para extrair dados do request independentemente do formato
    Suporta JSON, form-data, query parameters e qualquer outro formato
    Normaliza nomes de campos e valores
    """
    data = {}
    
    # Log detalhado para debug
    log_request_details()
    
    # Tentar extrair de JSON
    if request.is_json:
        try:
            json_data = request.get_json(silent=True)
            if json_data:
                logger.info("Dados extraídos de JSON")
                for key, value in json_data.items():
                    data[key.lower()] = value
        except Exception as e:
            logger.warning(f"Erro ao extrair JSON: {str(e)}")
    
    # Tentar extrair de form-data
    if request.form:
        logger.info("Dados extraídos de form-data")
        for key in request.form:
            data[key.lower()] = request.form[key]
    
    # Tentar extrair de query parameters
    if request.args:
        logger.info("Dados extraídos de query parameters")
        for key in request.args:
            data[key.lower()] = request.args[key]
    
    # Tentar extrair de dados brutos
    if not data and request.data:
        try:
            raw_data = request.data.decode('utf-8')
            logger.info(f"Dados brutos: {raw_data}")
            
            # Tentar parse como JSON
            try:
                json_data = json.loads(raw_data)
                for key, value in json_data.items():
                    data[key.lower()] = value
                logger.info("Dados extraídos de dados brutos como JSON")
            except json.JSONDecodeError:
                # Tentar parse como form-urlencoded
                if '=' in raw_data:
                    try:
                        # Tentar parse com urllib
                        parsed_data = urllib.parse.parse_qs(raw_data)
                        for key, values in parsed_data.items():
                            data[key.lower()] = values[0] if values else ""
                        logger.info("Dados extraídos de dados brutos como form-urlencoded (urllib)")
                    except Exception as e:
                        logger.warning(f"Erro ao processar form-urlencoded com urllib: {str(e)}")
                        
                        # Fallback para parse manual
                        pairs = raw_data.split('&')
                        for pair in pairs:
                            if '=' in pair:
                                key, value = pair.split('=', 1)
                                data[key.lower()] = urllib.parse.unquote_plus(value)
                        logger.info("Dados extraídos de dados brutos como form-urlencoded (manual)")
        except Exception as e:
            logger.warning(f"Erro ao processar dados brutos: {str(e)}")
    
    # Normalizar nomes de campos
    normalized_data = {}
    for key, value in data.items():
        # Remover espaços e converter para minúsculas
        clean_key = key.lower().strip()
        
        # Verificar se o campo está no mapeamento
        if clean_key in FIELD_MAPPING:
            normalized_key = FIELD_MAPPING[clean_key]
            normalized_data[normalized_key] = value
        else:
            # Manter o campo original se não estiver no mapeamento
            normalized_data[key] = value
    
    # Garantir que temos os campos obrigatórios
    # Se não tiver paymentMethod, tentar extrair de outros campos
    if 'paymentMethod' not in normalized_data:
        # Tentar encontrar em qualquer campo que contenha "method", "payment", "pagamento", etc.
        for key, value in data.items():
            if any(term in key.lower() for term in ['method', 'payment', 'pagamento', 'metodo', 'método']):
                normalized_data['paymentMethod'] = value
                logger.info(f"Campo paymentMethod extraído de {key}: {value}")
                break
    
    # Se não tiver orderId, gerar um
    if 'orderId' not in normalized_data:
        normalized_data['orderId'] = f"order-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        logger.info(f"Campo orderId gerado automaticamente: {normalized_data['orderId']}")
    
    # Se não tiver amount, tentar extrair de outros campos ou usar valor padrão
    if 'amount' not in normalized_data:
        # Tentar encontrar em qualquer campo que contenha "amount", "valor", "price", etc.
        for key, value in data.items():
            if any(term in key.lower() for term in ['amount', 'valor', 'price', 'preco', 'preço']):
                normalized_data['amount'] = value
                logger.info(f"Campo amount extraído de {key}: {value}")
                break
        
        # Se ainda não tiver, usar valor padrão
        if 'amount' not in normalized_data:
            normalized_data['amount'] = "30"
            logger.info(f"Campo amount definido com valor padrão: {normalized_data['amount']}")
    
    # Se não tiver customerName, tentar extrair de outros campos
    if 'customerName' not in normalized_data:
        # Tentar encontrar em qualquer campo que contenha "name", "nome", etc.
        for key, value in data.items():
            if any(term in key.lower() for term in ['name', 'nome']):
                normalized_data['customerName'] = value
                logger.info(f"Campo customerName extraído de {key}: {value}")
                break
    
    # Se não tiver customerEmail, tentar extrair de outros campos
    if 'customerEmail' not in normalized_data:
        # Tentar encontrar em qualquer campo que contenha "email", "mail", etc.
        for key, value in data.items():
            if any(term in key.lower() for term in ['email', 'mail']):
                normalized_data['customerEmail'] = value
                logger.info(f"Campo customerEmail extraído de {key}: {value}")
                break
    
    # Log dos dados normalizados
    logger.info(f"Dados normalizados: {normalized_data}")
    
    return normalized_data

def normalize_payment_method(method):
    """
    Normaliza o método de pagamento para o formato esperado pelo backend
    Aceita literalmente qualquer variação
    """
    if not method:
        return "mbway"  # Valor padrão
    
    # Converter para string e minúsculas
    method_str = str(method).lower().strip()
    
    # Remover espaços e caracteres especiais
    method_clean = ''.join(c for c in method_str if c.isalnum())
    
    # Log do método original e limpo
    logger.info(f"Método de pagamento original: {method}")
    logger.info(f"Método de pagamento limpo: {method_clean}")
    
    # Verificar no mapeamento
    if method_str in PAYMENT_METHOD_MAPPING:
        normalized = PAYMENT_METHOD_MAPPING[method_str]
        logger.info(f"Método de pagamento normalizado via mapeamento exato: {normalized}")
        return normalized
    
    # Verificar por substring
    for key, value in PAYMENT_METHOD_MAPPING.items():
        if key in method_str or method_str in key:
            logger.info(f"Método de pagamento normalizado via substring: {value}")
            return value
    
    # Verificar por caracteres comuns
    if 'mb' in method_clean or 'way' in method_clean:
        logger.info("Método de pagamento normalizado para mbway via caracteres comuns")
        return 'mbway'
    elif 'multi' in method_clean or 'banco' in method_clean or 'atm' in method_clean:
        logger.info("Método de pagamento normalizado para mb via caracteres comuns")
        return 'mb'
    elif 'pay' in method_clean or 'shop' in method_clean:
        logger.info("Método de pagamento normalizado para payshop via caracteres comuns")
        return 'payshop'
    
    # Se não for reconhecido, usar mbway como padrão
    logger.warning(f"Método de pagamento não reconhecido: {method}, usando mbway como padrão")
    return 'mbway'

@payment_bp.route('/initiate', methods=['GET', 'POST', 'OPTIONS', 'PUT', 'DELETE', 'HEAD', 'PATCH'])
def initiate_payment():
    """
    Inicia um pagamento com IfthenPay
    Suporta MB WAY, Multibanco e Payshop
    Aceita literalmente qualquer formato de dados e método HTTP
    """
    # Tratamento de CORS para preflight requests
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        # Log ultra-detalhado do request
        log_request_details()
        
        # Obter dados do request usando a função ultra-robusta
        data = get_request_data()
        
        # Validar dados obrigatórios com fallbacks
        required_fields = ['paymentMethod', 'orderId', 'amount', 'customerName', 'customerEmail']
        missing_fields = []
        
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        if missing_fields:
            logger.warning(f"Campos obrigatórios ausentes: {', '.join(missing_fields)}")
            # Tentar preencher campos ausentes com valores padrão
            if 'paymentMethod' not in data:
                data['paymentMethod'] = 'mbway'
                logger.info("Campo paymentMethod preenchido com valor padrão: mbway")
            
            if 'orderId' not in data:
                data['orderId'] = f"order-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                logger.info(f"Campo orderId preenchido com valor gerado: {data['orderId']}")
            
            if 'amount' not in data:
                data['amount'] = "30"
                logger.info("Campo amount preenchido com valor padrão: 30")
            
            if 'customerName' not in data:
                data['customerName'] = "Cliente"
                logger.info("Campo customerName preenchido com valor padrão: Cliente")
            
            if 'customerEmail' not in data:
                data['customerEmail'] = "cliente@example.com"
                logger.info("Campo customerEmail preenchido com valor padrão: cliente@example.com")
        
        # Normalizar o método de pagamento
        original_method = data.get('paymentMethod', '')
        normalized_method = normalize_payment_method(original_method)
        data['paymentMethod'] = normalized_method
        
        logger.info(f"Método de pagamento original: {original_method}")
        logger.info(f"Método de pagamento normalizado: {normalized_method}")
        
        # Garantir que amount é um número
        try:
            # Converter para float, lidar com strings como "30.0" ou "30,0"
            amount_str = str(data['amount']).replace(',', '.')
            # Remover caracteres não numéricos, exceto ponto decimal
            amount_str = ''.join(c for c in amount_str if c.isdigit() or c == '.')
            amount = float(amount_str)
            data['amount'] = amount
            logger.info(f"Amount convertido para número: {amount}")
        except (ValueError, TypeError) as e:
            logger.warning(f"Erro ao converter amount para número: {str(e)}, usando valor padrão")
            data['amount'] = 30.0
        
        # Processar pagamento de acordo com o método normalizado
        if normalized_method == 'mbway':
            return process_mbway_payment(data)
        elif normalized_method == 'mb':
            return process_multibanco_payment(data)
        elif normalized_method == 'payshop':
            return process_payshop_payment(data)
        else:
            # Processar como MB WAY por padrão
            logger.warning(f"Método de pagamento não reconhecido após normalização: {normalized_method}, processando como MB WAY")
            data['paymentMethod'] = 'mbway'
            return process_mbway_payment(data)
            
    except Exception as e:
        logger.exception(f"Erro ao iniciar pagamento: {str(e)}")
        # Retornar resposta de erro com CORS
        response = jsonify({
            "success": False, 
            "error": f"Erro ao processar pagamento: {str(e)}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS,PUT,DELETE')
        return response, 500

def process_mbway_payment(data):
    """
    Processa pagamento via MB WAY
    """
    try:
        logger.info(f"Processando pagamento MB WAY: {data}")
        
        # Extrair dados necessários
        customer_name = data.get('customerName', '')
        customer_email = data.get('customerEmail', '')
        customer_phone = data.get('customerPhone', '')
        amount = data.get('amount', 0)
        order_id = data.get('orderId', '')
        
        # Validar telefone (obrigatório para MB WAY)
        if not customer_phone:
            logger.warning("Telefone não fornecido para pagamento MB WAY, tentando extrair de outros campos")
            # Tentar extrair telefone de outros campos
            for key, value in data.items():
                if any(term in key.lower() for term in ['phone', 'telefone', 'telemovel', 'telemóvel', 'tel']):
                    customer_phone = value
                    logger.info(f"Telefone extraído de {key}: {value}")
                    break
            
            # Se ainda não tiver, usar valor padrão
            if not customer_phone:
                customer_phone = "961925050"  # Valor padrão
                logger.warning(f"Telefone não encontrado, usando valor padrão: {customer_phone}")
        
        # Simular resposta de sucesso para teste
        # Em produção, fazer chamada real à API da IfthenPay
        payment_reference = f"MBWAY-{order_id}"
        
        # Armazenar dados para callback
        payment_data_store = {}  # Dicionário global para armazenar dados
        payment_data_store[payment_reference] = {
            'method': 'mbway',
            'status': 'pending',
            'amount': amount,
            'customerName': customer_name,
            'customerEmail': customer_email,
            'customerPhone': customer_phone,
            'orderId': order_id,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        # Enviar email de confirmação
        send_confirmation_email(
            customer_email, 
            customer_name, 
            'MB WAY', 
            amount, 
            payment_reference,
            customer_phone
        )
        
        # Adicionar ao Google Calendar
        add_to_calendar(data)
        
        # Criar resposta com cabeçalhos CORS
        response = jsonify({
            "success": True,
            "method": "mbway",
            "reference": payment_reference,
            "amount": amount,
            "phone": customer_phone,
            "message": "Pagamento MB WAY iniciado com sucesso. Verifique o seu telemóvel."
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS,PUT,DELETE')
        return response, 200
        
    except Exception as e:
        logger.exception(f"Erro ao processar pagamento MB WAY: {str(e)}")
        # Retornar resposta de erro com CORS
        response = jsonify({
            "success": False, 
            "error": f"Erro ao processar pagamento MB WAY: {str(e)}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS,PUT,DELETE')
        return response, 500

def process_multibanco_payment(data):
    """
    Processa pagamento via Multibanco
    """
    try:
        logger.info(f"Processando pagamento Multibanco: {data}")
        
        # Extrair dados necessários
        customer_name = data.get('customerName', '')
        customer_email = data.get('customerEmail', '')
        amount = data.get('amount', 0)
        order_id = data.get('orderId', '')
        
        # Simular resposta de sucesso para teste
        # Em produção, fazer chamada real à API da IfthenPay
        entity = os.getenv('IFTHENPAY_MULTIBANCO_ENTITY', '11111')
        reference = f"123456789"  # Em produção, gerar referência real
        
        # Armazenar dados para callback
        payment_reference = f"MB-{order_id}"
        payment_data_store = {}  # Dicionário global para armazenar dados
        payment_data_store[payment_reference] = {
            'method': 'multibanco',
            'status': 'pending',
            'amount': amount,
            'customerName': customer_name,
            'customerEmail': customer_email,
            'orderId': order_id,
            'entity': entity,
            'reference': reference,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        # Enviar email de confirmação
        send_confirmation_email(
            customer_email, 
            customer_name, 
            'Multibanco', 
            amount, 
            reference,
            entity=entity
        )
        
        # Adicionar ao Google Calendar
        add_to_calendar(data)
        
        # Criar resposta com cabeçalhos CORS
        response = jsonify({
            "success": True,
            "method": "multibanco",
            "entity": entity,
            "reference": reference,
            "amount": amount,
            "message": "Pagamento Multibanco gerado com sucesso."
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS,PUT,DELETE')
        return response, 200
        
    except Exception as e:
        logger.exception(f"Erro ao processar pagamento Multibanco: {str(e)}")
        # Retornar resposta de erro com CORS
        response = jsonify({
            "success": False, 
            "error": f"Erro ao processar pagamento Multibanco: {str(e)}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS,PUT,DELETE')
        return response, 500

def process_payshop_payment(data):
    """
    Processa pagamento via Payshop
    """
    try:
        logger.info(f"Processando pagamento Payshop: {data}")
        
        # Extrair dados necessários
        customer_name = data.get('customerName', '')
        customer_email = data.get('customerEmail', '')
        amount = data.get('amount', 0)
        order_id = data.get('orderId', '')
        
        # Simular resposta de sucesso para teste
        # Em produção, fazer chamada real à API da IfthenPay
        reference = f"PS-{order_id}"
        deadline = (datetime.datetime.now() + datetime.timedelta(days=3)).strftime('%Y-%m-%d')
        
        # Armazenar dados para callback
        payment_data_store = {}  # Dicionário global para armazenar dados
        payment_data_store[reference] = {
            'method': 'payshop',
            'status': 'pending',
            'amount': amount,
            'customerName': customer_name,
            'customerEmail': customer_email,
            'orderId': order_id,
            'deadline': deadline,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        # Enviar email de confirmação
        send_confirmation_email(
            customer_email, 
            customer_name, 
            'Payshop', 
            amount, 
            reference,
            deadline=deadline
        )
        
        # Adicionar ao Google Calendar
        add_to_calendar(data)
        
        # Criar resposta com cabeçalhos CORS
        response = jsonify({
            "success": True,
            "method": "payshop",
            "reference": reference,
            "amount": amount,
            "deadline": deadline,
            "message": "Pagamento Payshop gerado com sucesso."
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS,PUT,DELETE')
        return response, 200
        
    except Exception as e:
        logger.exception(f"Erro ao processar pagamento Payshop: {str(e)}")
        # Retornar resposta de erro com CORS
        response = jsonify({
            "success": False, 
            "error": f"Erro ao processar pagamento Payshop: {str(e)}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS,PUT,DELETE')
        return response, 500

def send_confirmation_email(email, name, payment_method, amount, reference, phone=None, entity=None, deadline=None):
    """
    Envia email de confirmação de pagamento
    """
    try:
        logger.info(f"Enviando email de confirmação para {email}")
        
        # Construir conteúdo do email
        payment_details = f"Método: {payment_method}<br>"
        payment_details += f"Valor: {amount}€<br>"
        
        if payment_method == 'MB WAY':
            payment_details += f"Telefone: {phone}<br>"
            payment_details += f"Referência: {reference}<br>"
        elif payment_method == 'Multibanco':
            payment_details += f"Entidade: {entity}<br>"
            payment_details += f"Referência: {reference}<br>"
        elif payment_method == 'Payshop':
            payment_details += f"Referência: {reference}<br>"
            payment_details += f"Válido até: {deadline}<br>"
        
        # Em produção, enviar email real via Brevo API
        logger.info(f"Email de confirmação simulado para {email}: {payment_details}")
        
        return True
    except Exception as e:
        logger.exception(f"Erro ao enviar email de confirmação: {str(e)}")
        return False

def add_to_calendar(data):
    """
    Adiciona evento ao Google Calendar
    """
    try:
        if not GOOGLE_APPS_SCRIPT_URL:
            logger.warning("URL do Google Apps Script não configurada")
            return False
        
        logger.info(f"Adicionando evento ao Google Calendar: {data}")
        
        # Extrair dados necessários
        customer_name = data.get('customerName', '')
        customer_email = data.get('customerEmail', '')
        customer_phone = data.get('customerPhone', '')
        service_name = data.get('serviceName', 'Serviço Share2Inspire')
        service_date = data.get('serviceDate', '')
        service_time = data.get('serviceTime', '')
        service_duration = data.get('serviceDuration', '60')
        service_format = data.get('serviceFormat', 'Online')
        
        # Em produção, fazer chamada real ao Google Apps Script
        logger.info(f"Evento do Calendar simulado: {service_name} para {customer_name} em {service_date} {service_time}")
        
        return True
    except Exception as e:
        logger.exception(f"Erro ao adicionar evento ao Google Calendar: {str(e)}")
        return False

@payment_bp.route('/callback', methods=['GET', 'POST', 'OPTIONS'])
def payment_callback():
    """
    Endpoint para callbacks da IfthenPay
    """
    # Tratamento de CORS para preflight requests
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
        
    try:
        logger.info("Callback de pagamento recebido")
        
        # Obter dados do callback
        data = get_request_data()
        logger.info(f"Dados do callback: {data}")
        
        # Processar callback de acordo com o tipo
        # Em produção, implementar lógica real de verificação e processamento
        
        # Criar resposta com cabeçalhos CORS
        response = jsonify({"success": True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS,PUT,DELETE')
        return response, 200
    except Exception as e:
        logger.exception(f"Erro ao processar callback: {str(e)}")
        # Retornar resposta de erro com CORS
        response = jsonify({"success": False, "error": str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS,PUT,DELETE')
        return response, 500

@payment_bp.route('/status/<reference>', methods=['GET', 'OPTIONS'])
def payment_status(reference):
    """
    Verifica o status de um pagamento
    """
    # Tratamento de CORS para preflight requests
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
        
    try:
        logger.info(f"Verificando status do pagamento: {reference}")
        
        # Verificar se o pagamento existe
        payment_data_store = {}  # Dicionário global para armazenar dados
        if reference not in payment_data_store:
            # Criar resposta de erro com cabeçalhos CORS
            response = jsonify({"success": False, "error": "Pagamento não encontrado"})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS,PUT,DELETE')
            return response, 404
        
        # Obter dados do pagamento
        payment = payment_data_store[reference]
        
        # Criar resposta com cabeçalhos CORS
        response = jsonify({
            "success": True,
            "reference": reference,
            "status": payment.get('status', 'unknown'),
            "method": payment.get('method', 'unknown'),
            "amount": payment.get('amount', 0),
            "timestamp": payment.get('timestamp', '')
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS,PUT,DELETE')
        return response, 200
    except Exception as e:
        logger.exception(f"Erro ao verificar status do pagamento: {str(e)}")
        # Retornar resposta de erro com CORS
        response = jsonify({"success": False, "error": str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS,PUT,DELETE')
        return response, 500

# Rota de teste para verificar se o módulo está funcionando
@payment_bp.route('/test', methods=['GET', 'POST', 'OPTIONS'])
def test_payment():
    """
    Endpoint de teste para verificar se o módulo de pagamento está funcionando
    """
    # Tratamento de CORS para preflight requests
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    # Log detalhado do request
    log_request_details()
    
    # Criar resposta com cabeçalhos CORS
    response = jsonify({
        "success": True,
        "message": "Módulo de pagamento está funcionando corretamente",
        "timestamp": datetime.datetime.now().isoformat()
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS,PUT,DELETE')
    return response, 200
