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
                data['customerEmail'] = "cliente@exemplo.com"
                logger.info("Campo customerEmail preenchido com valor padrão: cliente@exemplo.com")
        
        # Normalizar método de pagamento
        payment_method = normalize_payment_method(data.get('paymentMethod'))
        data['paymentMethod'] = payment_method
        
        # Garantir que amount é um número
        try:
            amount = float(data.get('amount', 0))
            # Arredondar para 2 casas decimais
            amount = round(amount, 2)
            data['amount'] = str(amount)
        except (ValueError, TypeError):
            logger.warning(f"Valor inválido para amount: {data.get('amount')}, usando 30 como padrão")
            data['amount'] = "30"
            amount = 30.0
        
        # Verificar se temos telefone para MB WAY
        if payment_method == 'mbway' and 'customerPhone' not in data:
            logger.warning("Método de pagamento MB WAY selecionado, mas telefone não fornecido")
            # Tentar encontrar em qualquer campo que contenha "phone", "telefone", etc.
            phone_found = False
            for key, value in data.items():
                if any(term in key.lower() for term in ['phone', 'telefone', 'telemovel', 'telemóvel', 'tel']):
                    data['customerPhone'] = value
                    logger.info(f"Campo customerPhone extraído de {key}: {value}")
                    phone_found = True
                    break
            
            if not phone_found:
                logger.error("Telefone não encontrado para pagamento MB WAY")
                return jsonify({
                    "success": False,
                    "message": "Telefone obrigatório para pagamento MB WAY"
                }), 400
        
        # Processar pagamento de acordo com o método
        if payment_method == 'mbway':
            # Processar pagamento MB WAY
            return process_mbway_payment(data)
        elif payment_method == 'mb':
            # Processar pagamento Multibanco
            return process_multibanco_payment(data)
        elif payment_method == 'payshop':
            # Processar pagamento Payshop
            return process_payshop_payment(data)
        else:
            # Método de pagamento não suportado
            logger.error(f"Método de pagamento não suportado: {payment_method}")
            return jsonify({
                "success": False,
                "message": f"Método de pagamento não suportado: {payment_method}"
            }), 400
    
    except Exception as e:
        # Log detalhado do erro
        logger.error(f"Erro ao processar pagamento: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Retornar erro
        return jsonify({
            "success": False,
            "message": f"Erro ao processar pagamento: {str(e)}"
        }), 500

def process_mbway_payment(data):
    """
    Processa pagamento MB WAY
    """
    try:
        # Log dos dados recebidos
        logger.info(f"Processando pagamento MB WAY: {data}")
        
        # Extrair dados necessários
        amount = data.get('amount', '30')
        phone = data.get('customerPhone', '')
        order_id = data.get('orderId', f"order-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
        description = f"Share2Inspire - {data.get('service', 'Serviço')}"
        
        # Limpar telefone (remover espaços, traços, parênteses, etc.)
        phone = ''.join(c for c in phone if c.isdigit())
        
        # Adicionar prefixo +351 se não tiver e for um número português
        if len(phone) == 9 and phone.startswith(('91', '92', '93', '96', '95', '96', '97')):
            phone = f"351{phone}"
        
        # Garantir que o telefone tem o formato correto
        if not phone.startswith('351'):
            phone = f"351{phone}"
        
        # Log do telefone formatado
        logger.info(f"Telefone formatado para MB WAY: {phone}")
        
        # Construir URL da API
        api_url = f"https://ifthenpay.com/api/mbway/payment/{IFTHENPAY_MBWAY_KEY}"
        
        # Construir payload
        payload = {
            "mbway": phone,
            "amount": amount,
            "reference": order_id,
            "description": description
        }
        
        # Log do payload
        logger.info(f"Payload para API MB WAY: {payload}")
        
        # Fazer requisição para a API
        response = requests.post(api_url, json=payload)
        
        # Log da resposta
        logger.info(f"Resposta da API MB WAY: {response.status_code} - {response.text}")
        
        # Verificar se a requisição foi bem-sucedida
        if response.status_code == 200:
            # Extrair dados da resposta
            response_data = response.json()
            
            # Verificar se a resposta contém os dados esperados
            if 'MBWayPaymentId' in response_data:
                # Salvar dados do pagamento
                payment_data_store[order_id] = {
                    'method': 'mbway',
                    'status': 'pending',
                    'amount': amount,
                    'phone': phone,
                    'order_id': order_id,
                    'payment_id': response_data.get('MBWayPaymentId'),
                    'timestamp': datetime.datetime.now().isoformat(),
                    'customer_name': data.get('customerName', ''),
                    'customer_email': data.get('customerEmail', ''),
                    'service': data.get('service', ''),
                    'service_date': data.get('serviceDate', ''),
                    'service_time': data.get('serviceTime', ''),
                    'service_format': data.get('format', '')
                }
                
                # Enviar email de confirmação
                try:
                    send_confirmation_email(data, {
                        'method': 'mbway',
                        'phone': phone,
                        'amount': amount
                    })
                except Exception as e:
                    logger.error(f"Erro ao enviar email de confirmação: {str(e)}")
                
                # Retornar sucesso
                return jsonify({
                    "success": True,
                    "message": "Pagamento MB WAY iniciado com sucesso",
                    "paymentMethod": "mbway",
                    "phone": phone,
                    "amount": amount,
                    "orderId": order_id,
                    "paymentId": response_data.get('MBWayPaymentId')
                }), 200
            else:
                # Erro na resposta da API
                logger.error(f"Erro na resposta da API MB WAY: {response_data}")
                return jsonify({
                    "success": False,
                    "message": f"Erro na resposta da API MB WAY: {response_data.get('Message', 'Erro desconhecido')}"
                }), 400
        else:
            # Erro na requisição
            logger.error(f"Erro na requisição para API MB WAY: {response.status_code} - {response.text}")
            return jsonify({
                "success": False,
                "message": f"Erro na requisição para API MB WAY: {response.status_code} - {response.text}"
            }), 400
    
    except Exception as e:
        # Log detalhado do erro
        logger.error(f"Erro ao processar pagamento MB WAY: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Retornar erro
        return jsonify({
            "success": False,
            "message": f"Erro ao processar pagamento MB WAY: {str(e)}"
        }), 500

def process_multibanco_payment(data):
    """
    Processa pagamento Multibanco
    """
    try:
        # Log dos dados recebidos
        logger.info(f"Processando pagamento Multibanco: {data}")
        
        # Extrair dados necessários
        amount = data.get('amount', '30')
        order_id = data.get('orderId', f"order-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
        
        # Construir URL da API
        api_url = f"https://ifthenpay.com/api/multibanco/reference/{IFTHENPAY_MULTIBANCO_KEY}"
        
        # Construir payload
        payload = {
            "amount": amount,
            "reference": order_id
        }
        
        # Log do payload
        logger.info(f"Payload para API Multibanco: {payload}")
        
        # Fazer requisição para a API
        response = requests.post(api_url, json=payload)
        
        # Log da resposta
        logger.info(f"Resposta da API Multibanco: {response.status_code} - {response.text}")
        
        # Verificar se a requisição foi bem-sucedida
        if response.status_code == 200:
            # Extrair dados da resposta
            response_data = response.json()
            
            # Verificar se a resposta contém os dados esperados
            if 'Entity' in response_data and 'Reference' in response_data:
                # Salvar dados do pagamento
                payment_data_store[order_id] = {
                    'method': 'multibanco',
                    'status': 'pending',
                    'amount': amount,
                    'order_id': order_id,
                    'entity': response_data.get('Entity'),
                    'reference': response_data.get('Reference'),
                    'timestamp': datetime.datetime.now().isoformat(),
                    'customer_name': data.get('customerName', ''),
                    'customer_email': data.get('customerEmail', ''),
                    'service': data.get('service', ''),
                    'service_date': data.get('serviceDate', ''),
                    'service_time': data.get('serviceTime', ''),
                    'service_format': data.get('format', '')
                }
                
                # Enviar email de confirmação
                try:
                    send_confirmation_email(data, {
                        'method': 'multibanco',
                        'entity': response_data.get('Entity'),
                        'reference': response_data.get('Reference'),
                        'amount': amount
                    })
                except Exception as e:
                    logger.error(f"Erro ao enviar email de confirmação: {str(e)}")
                
                # Retornar sucesso
                return jsonify({
                    "success": True,
                    "message": "Referência Multibanco gerada com sucesso",
                    "paymentMethod": "multibanco",
                    "entity": response_data.get('Entity'),
                    "reference": response_data.get('Reference'),
                    "amount": amount,
                    "orderId": order_id
                }), 200
            else:
                # Erro na resposta da API
                logger.error(f"Erro na resposta da API Multibanco: {response_data}")
                return jsonify({
                    "success": False,
                    "message": f"Erro na resposta da API Multibanco: {response_data.get('Message', 'Erro desconhecido')}"
                }), 400
        else:
            # Erro na requisição
            logger.error(f"Erro na requisição para API Multibanco: {response.status_code} - {response.text}")
            return jsonify({
                "success": False,
                "message": f"Erro na requisição para API Multibanco: {response.status_code} - {response.text}"
            }), 400
    
    except Exception as e:
        # Log detalhado do erro
        logger.error(f"Erro ao processar pagamento Multibanco: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Retornar erro
        return jsonify({
            "success": False,
            "message": f"Erro ao processar pagamento Multibanco: {str(e)}"
        }), 500

def process_payshop_payment(data):
    """
    Processa pagamento Payshop
    """
    try:
        # Log dos dados recebidos
        logger.info(f"Processando pagamento Payshop: {data}")
        
        # Extrair dados necessários
        amount = data.get('amount', '30')
        order_id = data.get('orderId', f"order-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
        
        # Construir URL da API
        api_url = f"https://ifthenpay.com/api/payshop/reference/{IFTHENPAY_PAYSHOP_KEY}"
        
        # Construir payload
        payload = {
            "amount": amount,
            "reference": order_id,
            "validity": "48"  # Validade em horas
        }
        
        # Log do payload
        logger.info(f"Payload para API Payshop: {payload}")
        
        # Fazer requisição para a API
        response = requests.post(api_url, json=payload)
        
        # Log da resposta
        logger.info(f"Resposta da API Payshop: {response.status_code} - {response.text}")
        
        # Verificar se a requisição foi bem-sucedida
        if response.status_code == 200:
            # Extrair dados da resposta
            response_data = response.json()
            
            # Verificar se a resposta contém os dados esperados
            if 'Reference' in response_data:
                # Salvar dados do pagamento
                payment_data_store[order_id] = {
                    'method': 'payshop',
                    'status': 'pending',
                    'amount': amount,
                    'order_id': order_id,
                    'reference': response_data.get('Reference'),
                    'timestamp': datetime.datetime.now().isoformat(),
                    'customer_name': data.get('customerName', ''),
                    'customer_email': data.get('customerEmail', ''),
                    'service': data.get('service', ''),
                    'service_date': data.get('serviceDate', ''),
                    'service_time': data.get('serviceTime', ''),
                    'service_format': data.get('format', '')
                }
                
                # Enviar email de confirmação
                try:
                    send_confirmation_email(data, {
                        'method': 'payshop',
                        'reference': response_data.get('Reference'),
                        'amount': amount
                    })
                except Exception as e:
                    logger.error(f"Erro ao enviar email de confirmação: {str(e)}")
                
                # Retornar sucesso
                return jsonify({
                    "success": True,
                    "message": "Referência Payshop gerada com sucesso",
                    "paymentMethod": "payshop",
                    "reference": response_data.get('Reference'),
                    "amount": amount,
                    "orderId": order_id
                }), 200
            else:
                # Erro na resposta da API
                logger.error(f"Erro na resposta da API Payshop: {response_data}")
                return jsonify({
                    "success": False,
                    "message": f"Erro na resposta da API Payshop: {response_data.get('Message', 'Erro desconhecido')}"
                }), 400
        else:
            # Erro na requisição
            logger.error(f"Erro na requisição para API Payshop: {response.status_code} - {response.text}")
            return jsonify({
                "success": False,
                "message": f"Erro na requisição para API Payshop: {response.status_code} - {response.text}"
            }), 400
    
    except Exception as e:
        # Log detalhado do erro
        logger.error(f"Erro ao processar pagamento Payshop: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Retornar erro
        return jsonify({
            "success": False,
            "message": f"Erro ao processar pagamento Payshop: {str(e)}"
        }), 500

def send_confirmation_email(data, payment_info):
    """
    Envia email de confirmação para o cliente
    """
    if not BREVO_API_KEY:
        logger.warning("BREVO_API_KEY não definida, email de confirmação não será enviado")
        return
    
    try:
        # Extrair dados necessários
        customer_name = data.get('customerName', '')
        customer_email = data.get('customerEmail', '')
        service = data.get('service', 'Serviço')
        service_date = data.get('serviceDate', '')
        service_time = data.get('serviceTime', '')
        service_format = data.get('format', '')
        
        # Construir URL da API
        api_url = "https://api.brevo.com/v3/smtp/email"
        
        # Construir payload
        payload = {
            "sender": {
                "name": BREVO_SENDER_NAME,
                "email": BREVO_SENDER_EMAIL
            },
            "to": [
                {
                    "email": customer_email,
                    "name": customer_name
                }
            ],
            "bcc": [
                {
                    "email": "samuel@share2inspire.pt",
                    "name": "Samuel Rolo"
                }
            ],
            "subject": f"Confirmação de Reserva - {service}",
            "htmlContent": get_email_template(data, payment_info)
        }
        
        # Fazer requisição para a API
        headers = {
            "accept": "application/json",
            "api-key": BREVO_API_KEY,
            "content-type": "application/json"
        }
        
        response = requests.post(api_url, json=payload, headers=headers)
        
        # Log da resposta
        logger.info(f"Resposta da API Brevo: {response.status_code} - {response.text}")
        
        # Verificar se a requisição foi bem-sucedida
        if response.status_code == 201:
            logger.info("Email de confirmação enviado com sucesso")
            return True
        else:
            logger.error(f"Erro ao enviar email de confirmação: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        # Log detalhado do erro
        logger.error(f"Erro ao enviar email de confirmação: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def get_email_template(data, payment_info):
    """
    Retorna o template HTML para o email de confirmação
    """
    # Extrair dados necessários
    customer_name = data.get('customerName', '')
    service = data.get('service', 'Serviço')
    service_date = data.get('serviceDate', '')
    service_time = data.get('serviceTime', '')
    service_format = data.get('format', '')
    amount = payment_info.get('amount', '')
    
    # Formatar data
    formatted_date = service_date
    try:
        if service_date:
            date_obj = datetime.datetime.strptime(service_date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%d/%m/%Y')
    except Exception as e:
        logger.warning(f"Erro ao formatar data: {str(e)}")
    
    # Formatar hora
    formatted_time = service_time
    try:
        if service_time:
            time_obj = datetime.datetime.strptime(service_time, '%H:%M')
            formatted_time = time_obj.strftime('%H:%M')
    except Exception as e:
        logger.warning(f"Erro ao formatar hora: {str(e)}")
    
    # Construir bloco de informações de pagamento
    payment_block = ""
    if payment_info.get('method') == 'mbway':
        payment_block = f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                <strong>Método de Pagamento:</strong>
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                MB WAY
            </td>
        </tr>
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                <strong>Telefone:</strong>
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                {payment_info.get('phone', '')}
            </td>
        </tr>
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                <strong>Valor:</strong>
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                {amount}€
            </td>
        </tr>
        <tr>
            <td colspan="2" style="padding: 10px; border-bottom: 1px solid #ddd;">
                <p>Foi enviado um pedido de pagamento para o seu telefone. Por favor, aceite o pagamento na aplicação MB WAY.</p>
            </td>
        </tr>
        """
    elif payment_info.get('method') == 'multibanco':
        payment_block = f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                <strong>Método de Pagamento:</strong>
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                Multibanco
            </td>
        </tr>
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                <strong>Entidade:</strong>
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                {payment_info.get('entity', '')}
            </td>
        </tr>
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                <strong>Referência:</strong>
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                {payment_info.get('reference', '')}
            </td>
        </tr>
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                <strong>Valor:</strong>
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                {amount}€
            </td>
        </tr>
        <tr>
            <td colspan="2" style="padding: 10px; border-bottom: 1px solid #ddd;">
                <p>A referência é válida por 48 horas. Por favor, efetue o pagamento em qualquer caixa multibanco ou homebanking.</p>
            </td>
        </tr>
        """
    elif payment_info.get('method') == 'payshop':
        payment_block = f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                <strong>Método de Pagamento:</strong>
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                Payshop
            </td>
        </tr>
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                <strong>Referência:</strong>
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                {payment_info.get('reference', '')}
            </td>
        </tr>
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                <strong>Valor:</strong>
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                {amount}€
            </td>
        </tr>
        <tr>
            <td colspan="2" style="padding: 10px; border-bottom: 1px solid #ddd;">
                <p>A referência é válida por 48 horas. Por favor, efetue o pagamento em qualquer agente Payshop.</p>
            </td>
        </tr>
        """
    
    # Construir template HTML
    template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Confirmação de Reserva - {service}</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="https://share2inspire.pt/images/logo.png" alt="Share2Inspire Logo" style="max-width: 200px;">
        </div>
        
        <div style="background-color: #f9f9f9; padding: 20px; border-radius: 5px;">
            <h1 style="color: #4a6eb5; margin-top: 0;">Confirmação de Reserva</h1>
            
            <p>Olá {customer_name},</p>
            
            <p>Obrigado por reservar o serviço <strong>{service}</strong>. Abaixo estão os detalhes da sua reserva:</p>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                        <strong>Serviço:</strong>
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                        {service}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                        <strong>Data:</strong>
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                        {formatted_date}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                        <strong>Hora:</strong>
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                        {formatted_time}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                        <strong>Formato:</strong>
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                        {service_format}
                    </td>
                </tr>
                
                {payment_block}
            </table>
            
            <p>Após a confirmação do pagamento, entraremos em contacto para confirmar os detalhes da sessão.</p>
            
            <p>Se tiver alguma dúvida, por favor responda a este email ou contacte-nos através do telefone <a href="tel:+351912345678">+351 912 345 678</a>.</p>
        </div>
        
        <div style="margin-top: 30px; text-align: center; font-size: 12px; color: #777;">
            <p>&copy; 2023 Share2Inspire. Todos os direitos reservados.</p>
            <p>
                <a href="https://share2inspire.pt" style="color: #4a6eb5; text-decoration: none;">share2inspire.pt</a> |
                <a href="mailto:samuel@share2inspire.pt" style="color: #4a6eb5; text-decoration: none;">samuel@share2inspire.pt</a> |
                <a href="tel:+351912345678" style="color: #4a6eb5; text-decoration: none;">+351 912 345 678</a>
            </p>
        </div>
    </body>
    </html>
    """
    
    return template

@payment_bp.route('/callback', methods=['GET', 'POST'])
def payment_callback():
    """
    Endpoint para receber callbacks de pagamento da IfthenPay
    """
    try:
        # Log detalhado do request
        log_request_details()
        
        # Obter dados do request
        data = get_request_data()
        
        # Log dos dados recebidos
        logger.info(f"Callback de pagamento recebido: {data}")
        
        # Extrair dados necessários
        payment_id = data.get('id', '')
        reference = data.get('reference', '')
        status = data.get('status', '')
        
        # Verificar se temos o ID do pagamento ou referência
        if not payment_id and not reference:
            logger.error("ID do pagamento ou referência não fornecidos no callback")
            return jsonify({
                "success": False,
                "message": "ID do pagamento ou referência não fornecidos"
            }), 400
        
        # Procurar pagamento no armazenamento
        payment_found = False
        order_id = None
        
        for oid, payment_data in payment_data_store.items():
            if (payment_id and payment_data.get('payment_id') == payment_id) or \
               (reference and payment_data.get('reference') == reference):
                payment_found = True
                order_id = oid
                
                # Atualizar status do pagamento
                payment_data_store[oid]['status'] = status
                
                # Log da atualização
                logger.info(f"Status do pagamento atualizado: {oid} -> {status}")
                
                # Se o pagamento foi confirmado, agendar no Google Calendar
                if status.lower() in ['paid', 'confirmed', 'success', 'completed']:
                    try:
                        schedule_in_calendar(payment_data_store[oid])
                    except Exception as e:
                        logger.error(f"Erro ao agendar no Google Calendar: {str(e)}")
                
                break
        
        if not payment_found:
            logger.warning(f"Pagamento não encontrado para ID {payment_id} ou referência {reference}")
        
        # Retornar sucesso
        return jsonify({
            "success": True,
            "message": "Callback processado com sucesso",
            "orderFound": payment_found,
            "orderId": order_id,
            "status": status
        }), 200
    
    except Exception as e:
        # Log detalhado do erro
        logger.error(f"Erro ao processar callback de pagamento: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Retornar erro
        return jsonify({
            "success": False,
            "message": f"Erro ao processar callback de pagamento: {str(e)}"
        }), 500

def schedule_in_calendar(payment_data):
    """
    Agenda a sessão no Google Calendar via Google Apps Script
    """
    if not GOOGLE_APPS_SCRIPT_URL:
        logger.warning("GOOGLE_APPS_SCRIPT_URL não definida, agendamento no Google Calendar não será realizado")
        return
    
    try:
        # Extrair dados necessários
        customer_name = payment_data.get('customer_name', '')
        customer_email = payment_data.get('customer_email', '')
        service = payment_data.get('service', '')
        service_date = payment_data.get('service_date', '')
        service_time = payment_data.get('service_time', '')
        service_format = payment_data.get('service_format', '')
        
        # Verificar se temos os dados mínimos necessários
        if not service_date or not service_time:
            logger.warning("Data ou hora não fornecidos para agendamento no Google Calendar")
            return
        
        # Construir payload
        payload = {
            "customerName": customer_name,
            "customerEmail": customer_email,
            "service": service,
            "date": service_date,
            "time": service_time,
            "format": service_format
        }
        
        # Log do payload
        logger.info(f"Payload para Google Apps Script: {payload}")
        
        # Fazer requisição para o Google Apps Script
        response = requests.post(GOOGLE_APPS_SCRIPT_URL, json=payload)
        
        # Log da resposta
        logger.info(f"Resposta do Google Apps Script: {response.status_code} - {response.text}")
        
        # Verificar se a requisição foi bem-sucedida
        if response.status_code == 200:
            logger.info("Agendamento no Google Calendar realizado com sucesso")
            return True
        else:
            logger.error(f"Erro ao agendar no Google Calendar: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        # Log detalhado do erro
        logger.error(f"Erro ao agendar no Google Calendar: {str(e)}")
        logger.error(traceback.format_exc())
        return False

@payment_bp.route('/status/<order_id>', methods=['GET'])
def payment_status(order_id):
    """
    Endpoint para verificar o status de um pagamento
    """
    try:
        # Verificar se o pagamento existe
        if order_id not in payment_data_store:
            return jsonify({
                "success": False,
                "message": f"Pagamento não encontrado para o ID {order_id}"
            }), 404
        
        # Obter dados do pagamento
        payment_data = payment_data_store[order_id]
        
        # Retornar status
        return jsonify({
            "success": True,
            "orderId": order_id,
            "status": payment_data.get('status', 'unknown'),
            "method": payment_data.get('method', ''),
            "amount": payment_data.get('amount', ''),
            "timestamp": payment_data.get('timestamp', '')
        }), 200
    
    except Exception as e:
        # Log detalhado do erro
        logger.error(f"Erro ao verificar status do pagamento: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Retornar erro
        return jsonify({
            "success": False,
            "message": f"Erro ao verificar status do pagamento: {str(e)}"
        }), 500

@payment_bp.route('/test', methods=['GET'])
def test_payment():
    """
    Endpoint de teste para verificar se o módulo de pagamento está funcionando
    """
    return jsonify({
        "success": True,
        "message": "Módulo de pagamento funcionando corretamente",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now().isoformat()
    }), 200
