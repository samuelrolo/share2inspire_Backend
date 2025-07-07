#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blueprint de Ifthenpay para Share2Inspire
Serve como proxy para as APIs oficiais da Ifthenpay
"""

import os
import logging
import requests
import json
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta

# Configurar logging
logger = logging.getLogger(__name__)

# Criar blueprint
ifthenpay_bp = Blueprint('ifthenpay', __name__)

# URLs oficiais das APIs Ifthenpay
IFTHENPAY_URLS = {
    'mbway': 'https://api.ifthenpay.com/spg/payment/mbway',
    'multibanco': 'https://api.ifthenpay.com/multibanco/reference/init',
    'payshop': 'https://api.ifthenpay.com/payshop/reference/init'
}

def get_api_keys():
    """
    Obtém as chaves da API Ifthenpay das variáveis de ambiente
    
    Returns:
        dict: Dicionário com as chaves da API
    """
    return {
        'mbway': os.getenv('IFTHENPAY_MBWAY_KEY'),
        'multibanco': os.getenv('IFTHENPAY_MULTIBANCO_KEY'),
        'payshop': os.getenv('IFTHENPAY_PAYSHOP_KEY'),
        'callback_secret': os.getenv('IFTHENPAY_CALLBACK_SECRET')
    }

def validate_payment_data(data, payment_method):
    """
    Valida os dados recebidos para processamento de pagamento
    
    Args:
        data (dict): Dados do pagamento
        payment_method (str): Método de pagamento (mbway, multibanco, payshop)
    
    Returns:
        tuple: (is_valid, error_message, normalized_data)
    """
    # Campos obrigatórios comuns
    common_fields = ['orderId', 'amount', 'customerName', 'customerEmail']
    
    # Campos específicos por método
    method_specific_fields = {
        'mbway': ['mobileNumber'],
        'multibanco': [],
        'payshop': []
    }
    
    required_fields = common_fields + method_specific_fields.get(payment_method, [])
    
    # Verificar campos obrigatórios
    for field in required_fields:
        if not data.get(field):
            return False, f"Campo obrigatório em falta: {field}", None
    
    # Validar formato do valor
    try:
        amount = float(data['amount'])
        if amount <= 0:
            return False, "O valor deve ser maior que zero", None
    except (ValueError, TypeError):
        return False, "Valor inválido", None
    
    # Validar número de telemóvel para MB WAY
    if payment_method == 'mbway':
        mobile = data['mobileNumber'].replace(' ', '').replace('+', '')
        if not mobile.isdigit() or len(mobile) < 9:
            return False, "Número de telemóvel inválido", None
    
    return True, None, data

def format_mbway_request(data, api_key):
    """
    Formata os dados para a API MB WAY da Ifthenpay
    
    Args:
        data (dict): Dados do pagamento
        api_key (str): Chave da API MB WAY
    
    Returns:
        dict: Dados formatados para a API
    """
    # Formatar número de telemóvel (remover espaços e adicionar código do país se necessário)
    mobile = data['mobileNumber'].replace(' ', '').replace('+', '')
    if not mobile.startswith('351') and len(mobile) == 9:
        mobile = '351' + mobile
    
    return {
        'mbWayKey': api_key,
        'orderId': data['orderId'],
        'amount': str(data['amount']),
        'mobileNumber': mobile,
        'email': data['customerEmail'],
        'description': data.get('description', f"Pagamento Share2Inspire - {data['orderId']}")
    }

def format_multibanco_request(data, api_key):
    """
    Formata os dados para a API Multibanco da Ifthenpay
    
    Args:
        data (dict): Dados do pagamento
        api_key (str): Chave da API Multibanco
    
    Returns:
        dict: Dados formatados para a API
    """
    return {
        'mbKey': api_key,
        'orderId': data['orderId'],
        'amount': str(data['amount'])
    }

def format_payshop_request(data, api_key):
    """
    Formata os dados para a API Payshop da Ifthenpay
    
    Args:
        data (dict): Dados do pagamento
        api_key (str): Chave da API Payshop
    
    Returns:
        dict: Dados formatados para a API
    """
    # Calcular data de validade (30 dias a partir de hoje)
    validade = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    return {
        'payshopkey': api_key,
        'id': data['orderId'],
        'valor': str(data['amount']),
        'validade': validade
    }

@ifthenpay_bp.route('/mbway', methods=['POST', 'OPTIONS'])
def process_mbway_payment():
    """
    Endpoint para processar pagamentos MB WAY
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados JSON não fornecidos'
            }), 400
        
        # Validar dados
        is_valid, error_message, validated_data = validate_payment_data(data, 'mbway')
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_message
            }), 400
        
        # Obter chave da API
        api_keys = get_api_keys()
        mbway_key = api_keys['mbway']
        
        if not mbway_key:
            logger.error("Chave MB WAY não configurada")
            return jsonify({
                'success': False,
                'error': 'Serviço temporariamente indisponível'
            }), 500
        
        # Formatar dados para a API Ifthenpay
        api_data = format_mbway_request(validated_data, mbway_key)
        
        # Fazer chamada à API Ifthenpay
        try:
            response = requests.post(
                IFTHENPAY_URLS['mbway'],
                json=api_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Pagamento MB WAY iniciado com sucesso: {validated_data['orderId']}")
                
                return jsonify({
                    'success': True,
                    'message': f"Pedido MB WAY enviado para {validated_data['mobileNumber']}",
                    'data': {
                        'orderId': validated_data['orderId'],
                        'amount': validated_data['amount'],
                        'mobileNumber': validated_data['mobileNumber'],
                        'status': result.get('Status', 'Pending'),
                        'requestId': result.get('RequestId', ''),
                        'message': result.get('Message', 'Confirme o pagamento na aplicação MB WAY')
                    }
                }), 200
            else:
                logger.error(f"Erro na API MB WAY: {response.status_code} - {response.text}")
                return jsonify({
                    'success': False,
                    'error': 'Erro ao processar pagamento MB WAY'
                }), 500
                
        except requests.RequestException as e:
            logger.error(f"Erro de conexão com API MB WAY: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Erro de comunicação com o serviço de pagamentos'
            }), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint /ifthenpay/mbway: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@ifthenpay_bp.route('/multibanco', methods=['POST', 'OPTIONS'])
def process_multibanco_payment():
    """
    Endpoint para processar pagamentos Multibanco
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados JSON não fornecidos'
            }), 400
        
        # Validar dados
        is_valid, error_message, validated_data = validate_payment_data(data, 'multibanco')
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_message
            }), 400
        
        # Obter chave da API
        api_keys = get_api_keys()
        multibanco_key = api_keys['multibanco']
        
        if not multibanco_key:
            logger.error("Chave Multibanco não configurada")
            return jsonify({
                'success': False,
                'error': 'Serviço temporariamente indisponível'
            }), 500
        
        # Formatar dados para a API Ifthenpay
        api_data = format_multibanco_request(validated_data, multibanco_key)
        
        # Fazer chamada à API Ifthenpay
        try:
            response = requests.post(
                IFTHENPAY_URLS['multibanco'],
                json=api_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Referência Multibanco gerada com sucesso: {validated_data['orderId']}")
                
                return jsonify({
                    'success': True,
                    'message': 'Referência Multibanco gerada com sucesso',
                    'data': {
                        'orderId': validated_data['orderId'],
                        'amount': validated_data['amount'],
                        'entity': result.get('Entity', ''),
                        'reference': result.get('Reference', ''),
                        'status': 'Pending',
                        'message': 'Efetue o pagamento num terminal Multibanco ou homebanking'
                    }
                }), 200
            else:
                logger.error(f"Erro na API Multibanco: {response.status_code} - {response.text}")
                return jsonify({
                    'success': False,
                    'error': 'Erro ao gerar referência Multibanco'
                }), 500
                
        except requests.RequestException as e:
            logger.error(f"Erro de conexão com API Multibanco: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Erro de comunicação com o serviço de pagamentos'
            }), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint /ifthenpay/multibanco: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@ifthenpay_bp.route('/payshop', methods=['POST', 'OPTIONS'])
def process_payshop_payment():
    """
    Endpoint para processar pagamentos Payshop
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados JSON não fornecidos'
            }), 400
        
        # Validar dados
        is_valid, error_message, validated_data = validate_payment_data(data, 'payshop')
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_message
            }), 400
        
        # Obter chave da API
        api_keys = get_api_keys()
        payshop_key = api_keys['payshop']
        
        if not payshop_key:
            logger.error("Chave Payshop não configurada")
            return jsonify({
                'success': False,
                'error': 'Serviço temporariamente indisponível'
            }), 500
        
        # Formatar dados para a API Ifthenpay
        api_data = format_payshop_request(validated_data, payshop_key)
        
        # Fazer chamada à API Ifthenpay
        try:
            response = requests.post(
                IFTHENPAY_URLS['payshop'],
                json=api_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Referência Payshop gerada com sucesso: {validated_data['orderId']}")
                
                return jsonify({
                    'success': True,
                    'message': 'Referência Payshop gerada com sucesso',
                    'data': {
                        'orderId': validated_data['orderId'],
                        'amount': validated_data['amount'],
                        'reference': result.get('Reference', ''),
                        'validade': api_data['validade'],
                        'status': 'Pending',
                        'message': 'Efetue o pagamento num agente Payshop ou CTT'
                    }
                }), 200
            else:
                logger.error(f"Erro na API Payshop: {response.status_code} - {response.text}")
                return jsonify({
                    'success': False,
                    'error': 'Erro ao gerar referência Payshop'
                }), 500
                
        except requests.RequestException as e:
            logger.error(f"Erro de conexão com API Payshop: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Erro de comunicação com o serviço de pagamentos'
            }), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint /ifthenpay/payshop: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@ifthenpay_bp.route('/callback', methods=['POST', 'GET'])
def payment_callback():
    """
    Endpoint para receber callbacks da Ifthenpay sobre status de pagamentos
    """
    try:
        # Obter dados do callback
        if request.method == 'POST':
            data = request.get_json() or request.form.to_dict()
        else:
            data = request.args.to_dict()
        
        logger.info(f"Callback recebido da Ifthenpay: {data}")
        
        # Aqui você pode processar o callback e atualizar o status do pagamento
        # Por exemplo, enviar email de confirmação, atualizar base de dados, etc.
        
        return jsonify({
            'success': True,
            'message': 'Callback processado com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro no callback da Ifthenpay: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro ao processar callback'
        }), 500

@ifthenpay_bp.route('/health', methods=['GET'])
def ifthenpay_health_check():
    """
    Endpoint de verificação de saúde do serviço Ifthenpay
    """
    try:
        api_keys = get_api_keys()
        
        status = {
            'service': 'ifthenpay',
            'status': 'healthy',
            'mbway_configured': bool(api_keys['mbway']),
            'multibanco_configured': bool(api_keys['multibanco']),
            'payshop_configured': bool(api_keys['payshop']),
            'callback_configured': bool(api_keys['callback_secret'])
        }
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Erro no health check do Ifthenpay: {str(e)}")
        return jsonify({
            'service': 'ifthenpay',
            'status': 'unhealthy',
            'error': str(e)
        }), 500

