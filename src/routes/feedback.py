#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de processamento de feedback para Share2Inspire
Versão final que aceita múltiplos formatos de dados (JSON, FormData, URL params)
"""

import os
import json
import logging
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
feedback_bp = Blueprint('feedback', __name__)

# Configurações do Brevo
BREVO_API_KEY = os.getenv('BREVO_API_KEY')
BREVO_SENDER_NAME = os.getenv('BREVO_SENDER_NAME', 'Share2Inspire')
BREVO_SENDER_EMAIL = os.getenv('BREVO_SENDER_EMAIL', 'noreply@share2inspire.pt')

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

@feedback_bp.route('/submit', methods=['GET', 'POST', 'OPTIONS'])
def submit_feedback():
    """
    Recebe e processa feedback do usuário
    Aceita múltiplos formatos de dados (JSON, FormData, URL params)
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
        required_fields = ['name', 'email', 'message']
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
        
        # Extrair dados
        name = data.get('name', '')
        email = data.get('email', '')
        message = data.get('message', '')
        subject = data.get('subject', 'Feedback do Site')
        rating = data.get('rating', 5)  # Valor padrão de 5 estrelas se não for fornecido
        
        # Garantir que rating é um número
        try:
            rating = int(rating)
        except (ValueError, TypeError):
            rating = 5  # Valor padrão se a conversão falhar
        
        # Enviar email com o feedback
        success = send_feedback_email(name, email, subject, message, rating)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Feedback enviado com sucesso. Obrigado pelo seu contacto!"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Erro ao enviar feedback. Por favor, tente novamente mais tarde."
            }), 500
            
    except Exception as e:
        logger.exception(f"Erro ao processar feedback: {str(e)}")
        return jsonify({
            "success": False, 
            "error": f"Erro ao processar feedback: {str(e)}"
        }), 500

@feedback_bp.route('/contact', methods=['GET', 'POST', 'OPTIONS'])
def contact():
    """
    Recebe e processa mensagens de contacto
    Aceita múltiplos formatos de dados (JSON, FormData, URL params)
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
        required_fields = ['name', 'email', 'message']
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
        
        # Extrair dados
        name = data.get('name', '')
        email = data.get('email', '')
        message = data.get('message', '')
        subject = data.get('subject', 'Contacto do Site')
        
        # Enviar email com a mensagem de contacto
        success = send_contact_email(name, email, subject, message)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Mensagem enviada com sucesso. Entraremos em contacto brevemente!"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Erro ao enviar mensagem. Por favor, tente novamente mais tarde."
            }), 500
            
    except Exception as e:
        logger.exception(f"Erro ao processar contacto: {str(e)}")
        return jsonify({
            "success": False, 
            "error": f"Erro ao processar contacto: {str(e)}"
        }), 500

def send_feedback_email(name, email, subject, message, rating):
    """
    Envia email com o feedback recebido
    """
    try:
        logger.info(f"Enviando email de feedback de {email}")
        
        # Construir conteúdo do email
        email_subject = f"Novo Feedback: {subject}"
        email_content = f"""
        <h2>Novo Feedback Recebido</h2>
        <p><strong>Nome:</strong> {name}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Assunto:</strong> {subject}</p>
        <p><strong>Avaliação:</strong> {rating} estrelas</p>
        <p><strong>Mensagem:</strong></p>
        <p>{message}</p>
        """
        
        # Em produção, enviar email real via Brevo API
        if BREVO_API_KEY:
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {
                "accept": "application/json",
                "api-key": BREVO_API_KEY,
                "content-type": "application/json"
            }
            payload = {
                "sender": {
                    "name": BREVO_SENDER_NAME,
                    "email": BREVO_SENDER_EMAIL
                },
                "to": [
                    {
                        "email": "srshare2inspire@gmail.com",
                        "name": "Share2Inspire"
                    }
                ],
                "replyTo": {
                    "email": email,
                    "name": name
                },
                "subject": email_subject,
                "htmlContent": email_content
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 201:
                logger.info("Email de feedback enviado com sucesso")
                return True
            else:
                logger.error(f"Erro ao enviar email de feedback: {response.text}")
                return False
        else:
            # Simulação para ambiente de desenvolvimento
            logger.info(f"Email de feedback simulado: {email_subject}")
            logger.info(f"Conteúdo: {email_content}")
            return True
            
    except Exception as e:
        logger.exception(f"Erro ao enviar email de feedback: {str(e)}")
        return False

def send_contact_email(name, email, subject, message):
    """
    Envia email com a mensagem de contacto
    """
    try:
        logger.info(f"Enviando email de contacto de {email}")
        
        # Construir conteúdo do email
        email_subject = f"Nova Mensagem: {subject}"
        email_content = f"""
        <h2>Nova Mensagem Recebida</h2>
        <p><strong>Nome:</strong> {name}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Assunto:</strong> {subject}</p>
        <p><strong>Mensagem:</strong></p>
        <p>{message}</p>
        """
        
        # Em produção, enviar email real via Brevo API
        if BREVO_API_KEY:
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {
                "accept": "application/json",
                "api-key": BREVO_API_KEY,
                "content-type": "application/json"
            }
            payload = {
                "sender": {
                    "name": BREVO_SENDER_NAME,
                    "email": BREVO_SENDER_EMAIL
                },
                "to": [
                    {
                        "email": "srshare2inspire@gmail.com",
                        "name": "Share2Inspire"
                    }
                ],
                "replyTo": {
                    "email": email,
                    "name": name
                },
                "subject": email_subject,
                "htmlContent": email_content
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 201:
                logger.info("Email de contacto enviado com sucesso")
                return True
            else:
                logger.error(f"Erro ao enviar email de contacto: {response.text}")
                return False
        else:
            # Simulação para ambiente de desenvolvimento
            logger.info(f"Email de contacto simulado: {email_subject}")
            logger.info(f"Conteúdo: {email_content}")
            return True
            
    except Exception as e:
        logger.exception(f"Erro ao enviar email de contacto: {str(e)}")
        return False

@feedback_bp.route('/test', methods=['GET'])
def test_feedback():
    """
    Endpoint de teste para verificar se o módulo de feedback está funcionando
    """
    return jsonify({
        "success": True,
        "message": "Módulo de feedback está funcionando corretamente"
    }), 200
