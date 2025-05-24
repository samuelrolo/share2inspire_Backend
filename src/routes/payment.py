#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de processamento de pagamentos para Share2Inspire
Integração com IfthenPay (MB WAY, Multibanco, Payshop)
Inclui envio de email de confirmação e integração com Google Calendar
Versão final que aceita múltiplos formatos de dados e normaliza valores
"""

import os
import json
import logging
import datetime
import requests
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
# Importar handle_cors_preflight do main.py
from main import handle_cors_preflight

# Carregar variáveis de ambiente
load_dotenv()

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

def get_request_data():
    """
    Função universal para extrair dados do request independentemente do formato
    Suporta JSON, form-data e query parameters
    """
    data = {}
    
    # Log detalhado para debug
    logger.info(f"Content-Type: {request.headers.get('Content-Type', 'não especificado')}")
    logger.info(f"Request method: {request.method}")
    
    # Tentar extrair de JSON
    if request.is_json:
        try:
            json_data = request.get_json(silent=True)
            if json_data:
                logger.info("Dados extraídos de JSON")
                data.update(json_data)
        except Exception as e:
            logger.warning(f"Erro ao extrair JSON: {str(e)}")
    
    # Tentar extrair de form-data
    if request.form:
        logger.info("Dados extraídos de form-data")
        for key in request.form:
            data[key] = request.form[key]
    
    # Tentar extrair de query parameters
    if request.args:
        logger.info("Dados extraídos de query parameters")
        for key in request.args:
            data[key] = request.args[key]
    
    # Tentar extrair de dados brutos
    if not data and request.data:
        try:
            raw_data = request.data.decode('utf-8')
            logger.info(f"Dados brutos: {raw_data}")
            # Tentar parse como JSON
            try:
                json_data = json.loads(raw_data)
                data.update(json_data)
                logger.info("Dados extraídos de dados brutos como JSON")
            except json.JSONDecodeError:
                # Tentar parse como form-urlencoded
                if '=' in raw_data:
                    pairs = raw_data.split('&')
                    for pair in pairs:
                        if '=' in pair:
                            key, value = pair.split('=', 1)
                            data[key] = value
                    logger.info("Dados extraídos de dados brutos como form-urlencoded")
        except Exception as e:
            logger.warning(f"Erro ao processar dados brutos: {str(e)}")
    
    # Log dos dados extraídos
    logger.info(f"Dados extraídos: {data}")
    
    return data

def normalize_payment_method(method):
    """
    Normaliza o método de pagamento para o formato esperado pelo backend
    Aceita variações como 'MB WAY', 'MBWAY', 'mbway', etc.
    """
    if not method:
        return ""
    
    # Converter para string e minúsculas
    method_str = str(method).lower()
    
    # Remover espaços e caracteres especiais
    method_clean = ''.join(c for c in method_str if c.isalnum())
    
    # Mapear para os valores esperados
    if 'mbway' in method_clean or 'mb' == method_clean:
        return 'mbway'
    elif 'multibanco' in method_clean or 'mb' == method_clean:
        return 'mb'
    elif 'payshop' in method_clean:
        return 'payshop'
    
    # Se não for reconhecido, retornar o valor original limpo
    return method_clean

@payment_bp.route('/initiate', methods=['GET', 'POST', 'OPTIONS'])
def initiate_payment():
    """
    Inicia um pagamento com IfthenPay
    Suporta MB WAY, Multibanco e Payshop
    Aceita múltiplos formatos de dados e normaliza valores
    """
    # Tratamento de CORS para preflight requests
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        # Log de todos os headers para debug
        logger.info("Headers recebidos:")
        for header, value in request.headers.items():
            logger.info(f"{header}: {value}")
        
        # Obter dados do request usando a função universal
        data = get_request_data()
        
        # Validar dados obrigatórios
        required_fields = ['paymentMethod', 'orderId', 'amount', 'customerName', 'customerEmail']
        missing_fields = []
        
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        if missing_fields:
            logger.error(f"Campos obrigatórios ausentes: {', '.join(missing_fields)}")
            return jsonify({
                "success": False, 
                "error": f"Campos obrigatórios em falta: {', '.join(missing_fields)}"
            }), 400
        
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
            amount = float(amount_str)
            data['amount'] = amount
            logger.info(f"Amount convertido para número: {amount}")
        except (ValueError, TypeError) as e:
            logger.error(f"Erro ao converter amount para número: {str(e)}")
            return jsonify({
                "success": False, 
                "error": f"Valor inválido para amount: {data['amount']}"
            }), 400
        
        # Processar pagamento de acordo com o método normalizado
        if normalized_method == 'mbway':
            return process_mbway_payment(data)
        elif normalized_method == 'mb':
            return process_multibanco_payment(data)
        elif normalized_method == 'payshop':
            return process_payshop_payment(data)
        else:
            # Tentar processar como MB WAY por padrão se o método não for reconhecido
            logger.warning(f"Método de pagamento não reconhecido: {normalized_method}, tentando processar como MB WAY")
            data['paymentMethod'] = 'mbway'
            return process_mbway_payment(data)
            
    except Exception as e:
        logger.exception(f"Erro ao iniciar pagamento: {str(e)}")
        return jsonify({
            "success": False, 
            "error": f"Erro ao processar pagamento: {str(e)}"
        }), 500

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
            logger.error("Telefone obrigatório para pagamento MB WAY")
            return jsonify({
                "success": False, 
                "error": "Telefone obrigatório para pagamento MB WAY"
            }), 400
        
        # Simular resposta de sucesso para teste
        # Em produção, fazer chamada real à API da IfthenPay
        payment_reference = f"MBWAY-{order_id}"
        
        # Armazenar dados para callback
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
        
        return jsonify({
            "success": True,
            "method": "mbway",
            "reference": payment_reference,
            "amount": amount,
            "phone": customer_phone,
            "message": "Pagamento MB WAY iniciado com sucesso. Verifique o seu telemóvel."
        }), 200
        
    except Exception as e:
        logger.exception(f"Erro ao processar pagamento MB WAY: {str(e)}")
        return jsonify({
            "success": False, 
            "error": f"Erro ao processar pagamento MB WAY: {str(e)}"
        }), 500

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
        
        return jsonify({
            "success": True,
            "method": "multibanco",
            "entity": entity,
            "reference": reference,
            "amount": amount,
            "message": "Pagamento Multibanco gerado com sucesso."
        }), 200
        
    except Exception as e:
        logger.exception(f"Erro ao processar pagamento Multibanco: {str(e)}")
        return jsonify({
            "success": False, 
            "error": f"Erro ao processar pagamento Multibanco: {str(e)}"
        }), 500

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
        
        return jsonify({
            "success": True,
            "method": "payshop",
            "reference": reference,
            "amount": amount,
            "deadline": deadline,
            "message": "Pagamento Payshop gerado com sucesso."
        }), 200
        
    except Exception as e:
        logger.exception(f"Erro ao processar pagamento Payshop: {str(e)}")
        return jsonify({
            "success": False, 
            "error": f"Erro ao processar pagamento Payshop: {str(e)}"
        }), 500

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
        logger.exception(f"Erro ao adicionar evento ao Calendar: {str(e)}")
        return False

@payment_bp.route('/callback', methods=['GET', 'POST'])
def payment_callback():
    """
    Endpoint para callbacks da IfthenPay
    """
    try:
        logger.info("Callback de pagamento recebido")
        
        # Obter dados do request
        data = get_request_data()
        logger.info(f"Dados do callback: {data}")
        
        # Extrair referência e status
        reference = data.get('reference', '')
        status = data.get('status', '')
        
        if not reference:
            logger.error("Referência não fornecida no callback")
            return jsonify({"success": False, "error": "Referência não fornecida"}), 400
        
        # Verificar se a referência existe no armazenamento
        if reference not in payment_data_store:
            logger.error(f"Referência não encontrada: {reference}")
            return jsonify({"success": False, "error": "Referência não encontrada"}), 404
        
        # Atualizar status do pagamento
        payment_data_store[reference]['status'] = status
        logger.info(f"Status do pagamento atualizado: {reference} -> {status}")
        
        # Em produção, atualizar banco de dados e enviar notificações
        
        return jsonify({"success": True, "message": "Callback processado com sucesso"}), 200
    except Exception as e:
        logger.exception(f"Erro ao processar callback: {str(e)}")
        return jsonify({"success": False, "error": f"Erro ao processar callback: {str(e)}"}), 500

@payment_bp.route('/status/<reference>', methods=['GET'])
def payment_status(reference):
    """
    Verifica o status de um pagamento
    """
    try:
        logger.info(f"Verificando status do pagamento: {reference}")
        
        # Verificar se a referência existe no armazenamento
        if reference not in payment_data_store:
            logger.error(f"Referência não encontrada: {reference}")
            return jsonify({"success": False, "error": "Referência não encontrada"}), 404
        
        # Obter dados do pagamento
        payment_data = payment_data_store[reference]
        
        return jsonify({
            "success": True,
            "reference": reference,
            "status": payment_data['status'],
            "method": payment_data['method'],
            "amount": payment_data['amount'],
            "timestamp": payment_data['timestamp']
        }), 200
    except Exception as e:
        logger.exception(f"Erro ao verificar status do pagamento: {str(e)}")
        return jsonify({"success": False, "error": f"Erro ao verificar status: {str(e)}"}), 500
