#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serviço de Email para Share2Inspire - VERSÃO CORRIGIDA
Integra as funcionalidades de envio de email através de rotas HTTP
E-MAIL CORRIGIDO: share2inspire@gmail.com
"""

import os
import json
import logging
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Criar blueprint
email_bp = Blueprint('email', __name__)

# Configuração da API Brevo (Sendinblue)
configuration = sib_api_v3_sdk.Configuration()
api_key = os.getenv("BREVO_API_KEY")
configuration.api_key["api-key"] = api_key

# Verificar se a chave API foi carregada
if not api_key:
    logger.error("ALERTA: A variável de ambiente BREVO_API_KEY não está definida!")
else:
    logger.info("Chave API Brevo configurada com sucesso")

# Email do remetente verificado na Brevo - E-MAIL CORRIGIDO
VERIFIED_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL", "share2inspire@gmail.com")
VERIFIED_SENDER_NAME = os.getenv("BREVO_SENDER_NAME", "Share2Inspire")

# Email do destinatário (admin) - E-MAIL CORRIGIDO
ADMIN_EMAIL = "share2inspire@gmail.com"
ADMIN_NAME = "Share2Inspire Admin"

api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

def send_booking_confirmation_email(data):
    """
    Função principal para envio de emails de confirmação de reservas
    
    Args:
        data (dict): Dados da reserva contendo informações do cliente e serviço
    
    Returns:
        bool: True se o email foi enviado com sucesso, False caso contrário
    """
    try:
        logger.info(f"Enviando email de confirmação para {data.get('customerEmail')}")
        
        # Extrair dados
        customer_name = data.get('customerName', 'Cliente')
        customer_email = data.get('customerEmail')
        customer_phone = data.get('customerPhone', 'Não fornecido')
        appointment_date = data.get('appointmentDate', 'A definir')
        appointment_time = data.get('appointmentTime', 'A definir')
        service_description = data.get('description', 'Serviço Share2Inspire')
        order_id = data.get('orderId', f'order_{customer_name.replace(" ", "_")}')
        amount = data.get('amount', 0)
        method = data.get('method', 'email_booking')
        
        # Construir o email com formato melhorado
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": ADMIN_EMAIL, "name": ADMIN_NAME}],
            sender={"email": VERIFIED_SENDER_EMAIL, "name": VERIFIED_SENDER_NAME},
            subject=f"Nova Reserva - {service_description}",
            html_content=f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    h2 {{ color: #BF9A33; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                    .booking-details {{ background-color: #f9f9f9; padding: 15px; border-left: 4px solid #BF9A33; margin: 20px 0; }}
                    .footer {{ margin-top: 30px; font-size: 12px; color: #777; }}
                    .highlight {{ background-color: #fff3cd; padding: 10px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Nova Reserva Recebida</h2>
                    
                    <div class="booking-details">
                        <h3>Detalhes do Cliente</h3>
                        <p><strong>Nome:</strong> {customer_name}</p>
                        <p><strong>Email:</strong> {customer_email}</p>
                        <p><strong>Telefone:</strong> {customer_phone}</p>
                    </div>
                    
                    <div class="booking-details">
                        <h3>Detalhes da Reserva</h3>
                        <p><strong>Serviço:</strong> {service_description}</p>
                        <p><strong>Data:</strong> {appointment_date}</p>
                        <p><strong>Hora:</strong> {appointment_time}</p>
                        <p><strong>ID da Reserva:</strong> {order_id}</p>
                        <p><strong>Método:</strong> {method}</p>
                        {f'<p><strong>Valor:</strong> {amount}€</p>' if amount > 0 else ''}
                    </div>
                    
                    <div class="highlight">
                        <p><strong>Ação Necessária:</strong> Entre em contacto com o cliente para confirmar os detalhes da reserva.</p>
                    </div>
                    
                    <div class="footer">
                        <p>Este email foi enviado automaticamente pelo sistema Share2Inspire.</p>
                        <p>Data de envio: {{"{{date}}"}}</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            # Adicionar opções de rastreamento
            params={"date": "{{date}}"},
            headers={"Some-Custom-Header": "booking-confirmation"},
            # Configurar reply-to para o email do cliente
            reply_to={"email": customer_email, "name": customer_name}
        )
        
        # Enviar o email
        logger.info("A enviar email de confirmação via Brevo API")
        api_response = api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Email enviado com sucesso. ID da mensagem: {api_response.message_id}")
        
        return True
        
    except ApiException as e:
        # Tratamento específico de erros da API Brevo
        error_body = getattr(e, 'body', str(e))
        error_status = getattr(e, 'status', 500)
        logger.error(f"Erro na API Brevo: Status {error_status}, Corpo: {error_body}")
        return False
        
    except Exception as e:
        # Tratamento genérico de outros erros
        logger.exception(f"Erro inesperado ao enviar email de confirmação: {str(e)}")
        return False

def validate_email_data(data, service_type):
    """
    Valida os dados recebidos para envio de email
    
    Args:
        data (dict): Dados do formulário
        service_type (str): Tipo de serviço (kickstart, consultoria, etc.)
    
    Returns:
        tuple: (is_valid, error_message, normalized_data)
    """
    required_fields = ['customerName', 'customerEmail', 'customerPhone', 'appointmentDate', 'appointmentTime']
    
    # Verificar campos obrigatórios
    for field in required_fields:
        if not data.get(field):
            return False, f"Campo obrigatório em falta: {field}", None
    
    # Normalizar dados para o formato esperado pelo email_service
    normalized_data = {
        'customerName': data['customerName'],
        'customerEmail': data['customerEmail'],
        'customerPhone': data['customerPhone'],
        'appointmentDate': data['appointmentDate'],
        'appointmentTime': data['appointmentTime'],
        'orderId': data.get('orderId', f"{service_type}_{data['customerName'].replace(' ', '_')}_{data['appointmentDate']}"),
        'method': 'email_booking',  # Método específico para reservas por email
        'amount': data.get('amount', 0),
        'description': get_service_description(service_type),
        'entity': '',
        'reference': ''
    }
    
    return True, None, normalized_data

def get_service_description(service_type):
    """
    Retorna a descrição do serviço baseada no tipo
    
    Args:
        service_type (str): Tipo de serviço
    
    Returns:
        str: Descrição do serviço
    """
    descriptions = {
        'kickstart': 'Kickstart Pro - Sessão de Aceleração de Carreira',
        'consultoria': 'Consultoria Personalizada - Orientação Profissional',
        'coaching': 'Coaching Individual - Desenvolvimento Pessoal',
        'workshops': 'Workshop Especializado - Formação Prática',
        'contact': 'Contacto Geral - Informações e Esclarecimentos'
    }
    
    return descriptions.get(service_type, f'Serviço Share2Inspire - {service_type.title()}')

@email_bp.route('/kickstart', methods=['POST', 'OPTIONS'])
def send_kickstart_email():
    """
    Endpoint para envio de emails de confirmação do serviço Kickstart Pro
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
        is_valid, error_message, normalized_data = validate_email_data(data, 'kickstart')
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_message
            }), 400
        
        # Enviar email
        email_sent = send_booking_confirmation_email(normalized_data)
        
        if email_sent:
            logger.info(f"Email de Kickstart enviado com sucesso para {normalized_data['customerEmail']}")
            return jsonify({
                'success': True,
                'message': 'Email de confirmação enviado com sucesso',
                'orderId': normalized_data['orderId']
            }), 200
        else:
            logger.error(f"Falha ao enviar email de Kickstart para {normalized_data['customerEmail']}")
            return jsonify({
                'success': False,
                'error': 'Falha ao enviar email de confirmação'
            }), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint /email/kickstart: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@email_bp.route('/consultoria', methods=['POST', 'OPTIONS'])
def send_consultoria_email():
    """
    Endpoint para envio de emails de confirmação do serviço de Consultoria
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
        is_valid, error_message, normalized_data = validate_email_data(data, 'consultoria')
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_message
            }), 400
        
        # Enviar email
        email_sent = send_booking_confirmation_email(normalized_data)
        
        if email_sent:
            logger.info(f"Email de Consultoria enviado com sucesso para {normalized_data['customerEmail']}")
            return jsonify({
                'success': True,
                'message': 'Email de confirmação enviado com sucesso',
                'orderId': normalized_data['orderId']
            }), 200
        else:
            logger.error(f"Falha ao enviar email de Consultoria para {normalized_data['customerEmail']}")
            return jsonify({
                'success': False,
                'error': 'Falha ao enviar email de confirmação'
            }), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint /email/consultoria: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@email_bp.route('/coaching', methods=['POST', 'OPTIONS'])
def send_coaching_email():
    """
    Endpoint para envio de emails de confirmação do serviço de Coaching
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
        is_valid, error_message, normalized_data = validate_email_data(data, 'coaching')
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_message
            }), 400
        
        # Enviar email
        email_sent = send_booking_confirmation_email(normalized_data)
        
        if email_sent:
            logger.info(f"Email de Coaching enviado com sucesso para {normalized_data['customerEmail']}")
            return jsonify({
                'success': True,
                'message': 'Email de confirmação enviado com sucesso',
                'orderId': normalized_data['orderId']
            }), 200
        else:
            logger.error(f"Falha ao enviar email de Coaching para {normalized_data['customerEmail']}")
            return jsonify({
                'success': False,
                'error': 'Falha ao enviar email de confirmação'
            }), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint /email/coaching: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@email_bp.route('/workshops', methods=['POST', 'OPTIONS'])
def send_workshops_email():
    """
    Endpoint para envio de emails de confirmação do serviço de Workshops
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
        is_valid, error_message, normalized_data = validate_email_data(data, 'workshops')
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_message
            }), 400
        
        # Enviar email
        email_sent = send_booking_confirmation_email(normalized_data)
        
        if email_sent:
            logger.info(f"Email de Workshops enviado com sucesso para {normalized_data['customerEmail']}")
            return jsonify({
                'success': True,
                'message': 'Email de confirmação enviado com sucesso',
                'orderId': normalized_data['orderId']
            }), 200
        else:
            logger.error(f"Falha ao enviar email de Workshops para {normalized_data['customerEmail']}")
            return jsonify({
                'success': False,
                'error': 'Falha ao enviar email de confirmação'
            }), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint /email/workshops: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@email_bp.route('/contact', methods=['POST', 'OPTIONS'])
def send_contact_email():
    """
    Endpoint para envio de emails de contacto geral
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
        
        # Para contactos, os campos podem ser diferentes
        required_fields = ['customerName', 'customerEmail']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório em falta: {field}'
                }), 400
        
        # Normalizar dados para contacto
        normalized_data = {
            'customerName': data['customerName'],
            'customerEmail': data['customerEmail'],
            'customerPhone': data.get('customerPhone', 'Não fornecido'),
            'appointmentDate': data.get('appointmentDate', 'A definir'),
            'appointmentTime': data.get('appointmentTime', 'A definir'),
            'orderId': f"contact_{data['customerName'].replace(' ', '_')}",
            'method': 'contact_form',
            'amount': 0,
            'description': f"Contacto Geral - {data.get('message', 'Pedido de informações')}",
            'entity': '',
            'reference': ''
        }
        
        # Enviar email
        email_sent = send_booking_confirmation_email(normalized_data)
        
        if email_sent:
            logger.info(f"Email de contacto enviado com sucesso para {normalized_data['customerEmail']}")
            return jsonify({
                'success': True,
                'message': 'Mensagem de contacto enviada com sucesso',
                'orderId': normalized_data['orderId']
            }), 200
        else:
            logger.error(f"Falha ao enviar email de contacto para {normalized_data['customerEmail']}")
            return jsonify({
                'success': False,
                'error': 'Falha ao enviar mensagem de contacto'
            }), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint /email/contact: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@email_bp.route('/health', methods=['GET'])
def email_health_check():
    """
    Endpoint de verificação de saúde do serviço de email
    """
    try:
        # Verificar se as variáveis de ambiente estão configuradas
        brevo_key = os.getenv('BREVO_API_KEY')
        sender_email = os.getenv('BREVO_SENDER_EMAIL')
        
        status = {
            'service': 'email',
            'status': 'healthy',
            'brevo_configured': bool(brevo_key),
            'sender_configured': bool(sender_email),
            'admin_email': ADMIN_EMAIL,
            'sender_email': VERIFIED_SENDER_EMAIL
        }
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Erro no health check do email: {str(e)}")
        return jsonify({
            'service': 'email',
            'status': 'unhealthy',
            'error': str(e)
        }), 500

