#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de processamento de pagamentos para Share2Inspire
Integração com IfthenPay (MB WAY, Multibanco, Payshop)
Inclui envio de email de confirmação e integração com Google Calendar
"""

import os
import json
import logging
import datetime
import requests
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
# Importar handle_cors_preflight do main.py em vez de cors_fix
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

@payment_bp.route('/initiate', methods=['POST', 'OPTIONS'])
def initiate_payment():
    """
    Inicia um pagamento com IfthenPay
    Suporta MB WAY, Multibanco e Payshop
    """
    # Tratamento de CORS para preflight requests
    if request.method == 'OPTIONS':
        return handle_cors_preflight()
    
    try:
        # Obter dados do request
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['paymentMethod', 'orderId', 'amount', 'customerName', 'customerEmail']
        for field in required_fields:
            if field not in data:
                logger.error(f"Campo obrigatório ausente: {field}")
                return jsonify({"success": False, "error": f"Campo obrigatório ausente: {field}"}), 400
        
        # Obter método de pagamento
        payment_method = data.get('paymentMethod', '').lower()
        
        # Processar pagamento de acordo com o método
        if payment_method == 'mbway':
            return process_mbway_payment(data)
        elif payment_method == 'mb':
            return process_multibanco_payment(data)
        elif payment_method == 'payshop':
            return process_payshop_payment(data)
        else:
            logger.error(f"Método de pagamento não suportado: {payment_method}")
            return jsonify({"success": False, "error": "Método de pagamento não suportado"}), 400
            
    except Exception as e:
        logger.exception(f"Erro ao iniciar pagamento: {str(e)}")
        return jsonify({"success": False, "error": "Erro ao processar pagamento"}), 500

# Resto do código permanece o mesmo...
