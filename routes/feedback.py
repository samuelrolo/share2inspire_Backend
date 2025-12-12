# /home/ubuntu/share2inspire_backend/src/routes/feedback.py
import os
import json
import logging
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from dotenv import load_dotenv

from utils.secrets import get_secret

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente do ficheiro .env
load_dotenv()

feedback_bp = Blueprint("feedback", __name__, url_prefix="/api/feedback")

# Configuração da API Brevo (Sendinblue)
configuration = sib_api_v3_sdk.Configuration()
api_key = get_secret("BREVO_API_KEY")
configuration.api_key["api-key"] = api_key

# Verificar se a chave API foi carregada
if not api_key:
    logger.error("ALERTA: A variável de ambiente BREVO_API_KEY não está definida!")
else:
    logger.info("Chave API Brevo configurada com sucesso")

# Email do remetente verificado na Brevo - E-MAIL CORRIGIDO
VERIFIED_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL", "srshare2inspire@gmail.com")
VERIFIED_SENDER_NAME = os.getenv("BREVO_SENDER_NAME", "Share2Inspire")

# Email do destinatário (admin) - E-MAIL CORRIGIDO
ADMIN_EMAIL = "srshare2inspire@gmail.com"
ADMIN_NAME = "Share2Inspire Admin"

api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

# NOVA ROTA: Endpoint para contacto geral
@feedback_bp.route("/contact", methods=["POST", "OPTIONS"])
@cross_origin()
def submit_contact():
    """
    Endpoint para enviar mensagens de contacto via email usando a API Brevo.
    Recebe dados do formulário e envia um email transacional para o administrador.
    """
    # Tratar pedidos OPTIONS para CORS
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200
        
    try:
        data = request.get_json()
        logger.info(f"Dados de contacto recebidos: {json.dumps(data, indent=2)}")
        
        if not data:
            logger.warning("Nenhum dado recebido no corpo da requisição")
            return jsonify({"error": "Nenhum dado recebido"}), 400
            
        # Validação de campos obrigatórios
        required_fields = ["name", "email", "message"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            logger.warning(f"Campos obrigatórios em falta: {', '.join(missing_fields)}")
            return jsonify({
                "error": f"Campos obrigatórios em falta: {', '.join(missing_fields)}",
                "status": "error"
            }), 400
            
        name = data.get("name")
        email = data.get("email")
        message = data.get("message")
        subject = data.get("subject", "Contacto do Website")
        phone = data.get("phone", "Não fornecido")
        source = data.get("source", "website_contact")
        
        # Construir o email com formato melhorado
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": ADMIN_EMAIL, "name": ADMIN_NAME}],
            sender={"email": VERIFIED_SENDER_EMAIL, "name": VERIFIED_SENDER_NAME},
            subject=f"Nova Mensagem de Contacto: {subject}",
            html_content=f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    h2 {{ color: #BF9A33; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                    .message {{ background-color: #f9f9f9; padding: 15px; border-left: 4px solid #BF9A33; }}
                    .footer {{ margin-top: 30px; font-size: 12px; color: #777; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Nova Mensagem de Contacto</h2>
                    <p><strong>De:</strong> {name} ({email})</p>
                    <p><strong>Telefone:</strong> {phone}</p>
                    <p><strong>Assunto:</strong> {subject}</p>
                    <p><strong>Origem:</strong> {source}</p>
                    <p><strong>Data:</strong> {{"{{date}}"}}</p>
                    <div class="message">
                        <p><strong>Mensagem:</strong></p>
                        <p>{message}</p>
                    </div>
                    <div class="footer">
                        <p>Este email foi enviado automaticamente pelo sistema Share2Inspire.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            # Adicionar opções de rastreamento
            params={"date": "{{date}}"},
            headers={"Some-Custom-Header": "contact-notification"},
            # Configurar reply-to para o email do utilizador
            reply_to={"email": email, "name": name}
        )
        
        # Enviar o email
        logger.info("A enviar email de contacto via Brevo API")
        api_response = api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Email enviado com sucesso. ID da mensagem: {api_response.message_id}")
        
        return jsonify({
            "message": "Mensagem enviada com sucesso!",
            "status": "success",
            "messageId": api_response.message_id,
            "redirected": True
        }), 200
        
    except ApiException as e:
        # Tratamento específico de erros da API Brevo
        error_body = getattr(e, 'body', str(e))
        error_status = getattr(e, 'status', 500)
        logger.error(f"Erro na API Brevo: Status {error_status}, Corpo: {error_body}")
        
        # Mapear códigos de erro comuns para mensagens amigáveis
        error_messages = {
            400: "Dados inválidos no pedido. Verifique os campos e tente novamente.",
            401: "Erro de autenticação com a API Brevo. Verifique a chave API.",
            403: "Acesso negado à API Brevo. Verifique as permissões da chave API.",
            429: "Limite de envios excedido. Tente novamente mais tarde.",
            500: "Erro no servidor Brevo. Tente novamente mais tarde."
        }
        
        user_message = error_messages.get(error_status, "Ocorreu um erro ao enviar a mensagem. Tente novamente mais tarde.")
        
        return jsonify({
            "error": user_message,
            "status": "error",
            "details": str(error_body) if os.getenv("FLASK_ENV") == "development" else None
        }), error_status
        
    except Exception as e:
        # Tratamento genérico de outros erros
        logger.exception(f"Erro inesperado ao processar contacto: {str(e)}")
        
        return jsonify({
            "error": "Ocorreu um erro inesperado ao processar a sua mensagem. Por favor, tente novamente mais tarde.",
            "status": "error"
        }), 500

@feedback_bp.route("/submit", methods=["POST", "OPTIONS"])
@cross_origin()
def submit_feedback():
    """
    Endpoint para enviar feedback via email usando a API Brevo.
    Recebe dados do formulário e envia um email transacional para o administrador.
    """
    # Tratar pedidos OPTIONS para CORS
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200
        
    try:
        data = request.get_json()
        logger.info(f"Dados de feedback recebidos: {json.dumps(data, indent=2)}")
        
        if not data:
            logger.warning("Nenhum dado recebido no corpo da requisição")
            return jsonify({"error": "Nenhum dado recebido"}), 400
            
        # Validação de campos obrigatórios
        required_fields = ["rating", "message"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            logger.warning(f"Campos obrigatórios em falta: {', '.join(missing_fields)}")
            return jsonify({
                "error": f"Campos obrigatórios em falta: {', '.join(missing_fields)}",
                "status": "error"
            }), 400
            
        rating = data.get("rating")
        message = data.get("message")
        user_email = data.get("email", "Não fornecido")
        user_name = data.get("name", "Utilizador Anónimo")
        
        # Construir o email com formato melhorado
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": ADMIN_EMAIL, "name": ADMIN_NAME}],
            sender={"email": VERIFIED_SENDER_EMAIL, "name": VERIFIED_SENDER_NAME},
            subject="Novo Feedback Recebido - Share2Inspire",
            html_content=f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    h2 {{ color: #BF9A33; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                    .rating {{ font-size: 18px; font-weight: bold; margin: 15px 0; }}
                    .message {{ background-color: #f9f9f9; padding: 15px; border-left: 4px solid #BF9A33; }}
                    .footer {{ margin-top: 30px; font-size: 12px; color: #777; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Novo Feedback Recebido</h2>
                    <p><strong>De:</strong> {user_name} ({user_email})</p>
                    <p><strong>Data:</strong> {{"{{date}}"}}</p>
                    <div class="rating">
                        <p><strong>Avaliação:</strong> {rating} estrelas</p>
                    </div>
                    <div class="message">
                        <p><strong>Mensagem:</strong></p>
                        <p>{message}</p>
                    </div>
                    <div class="footer">
                        <p>Este email foi enviado automaticamente pelo sistema Share2Inspire.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            # Adicionar opções de rastreamento
            params={"date": "{{date}}"},
            headers={"Some-Custom-Header": "feedback-notification"},
            # Configurar reply-to para o email do utilizador se fornecido
            reply_to={"email": user_email, "name": user_name} if user_email != "Não fornecido" else None
        )
        
        # Enviar o email
        logger.info("A enviar email de feedback via Brevo API")
        api_response = api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Email enviado com sucesso. ID da mensagem: {api_response.message_id}")
        
        return jsonify({
            "message": "Feedback enviado com sucesso!",
            "status": "success",
            "messageId": api_response.message_id
        }), 200
        
    except ApiException as e:
        # Tratamento específico de erros da API Brevo
        error_body = getattr(e, 'body', str(e))
        error_status = getattr(e, 'status', 500)
        logger.error(f"Erro na API Brevo: Status {error_status}, Corpo: {error_body}")
        
        # Mapear códigos de erro comuns para mensagens amigáveis
        error_messages = {
            400: "Dados inválidos no pedido. Verifique os campos e tente novamente.",
            401: "Erro de autenticação com a API Brevo. Verifique a chave API.",
            403: "Acesso negado à API Brevo. Verifique as permissões da chave API.",
            429: "Limite de envios excedido. Tente novamente mais tarde.",
            500: "Erro no servidor Brevo. Tente novamente mais tarde."
        }
        
        user_message = error_messages.get(error_status, "Ocorreu um erro ao enviar o feedback. Tente novamente mais tarde.")
        
        return jsonify({
            "error": user_message,
            "status": "error",
            "details": str(error_body) if os.getenv("FLASK_ENV") == "development" else None
        }), error_status
        
    except Exception as e:
        # Tratamento genérico de outros erros
        logger.exception(f"Erro inesperado ao processar feedback: {str(e)}")
        
        return jsonify({
            "error": "Ocorreu um erro inesperado ao processar o seu feedback. Por favor, tente novamente mais tarde.",
            "status": "error"
        }), 500

@feedback_bp.route("/newsletter", methods=["POST", "OPTIONS"])
@cross_origin()
def submit_newsletter():
    """
    Endpoint para inscrição na newsletter via email usando a API Brevo.
    Recebe dados do formulário e envia um email de confirmação.
    """
    # Tratar pedidos OPTIONS para CORS
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200
        
    try:
        data = request.get_json()
        logger.info(f"Dados de newsletter recebidos: {json.dumps(data, indent=2)}")
        
        if not data:
            logger.warning("Nenhum dado recebido no corpo da requisição")
            return jsonify({"error": "Nenhum dado recebido"}), 400
            
        # Validação de campos obrigatórios
        required_fields = ["email"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            logger.warning(f"Campos obrigatórios em falta: {', '.join(missing_fields)}")
            return jsonify({
                "error": f"Campos obrigatórios em falta: {', '.join(missing_fields)}",
                "status": "error"
            }), 400
            
        user_email = data.get("email")
        user_name = data.get("name", "Subscritor")
        
        # Construir o email de confirmação para o administrador
        admin_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": ADMIN_EMAIL, "name": ADMIN_NAME}],
            sender={"email": VERIFIED_SENDER_EMAIL, "name": VERIFIED_SENDER_NAME},
            subject="Nova Subscrição de Newsletter - Share2Inspire",
            html_content=f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    h2 {{ color: #BF9A33; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                    .footer {{ margin-top: 30px; font-size: 12px; color: #777; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Nova Subscrição de Newsletter</h2>
                    <p><strong>De:</strong> {user_name} ({user_email})</p>
                    <p><strong>Data:</strong> {{"{{date}}"}}</p>
                    <div class="footer">
                        <p>Este email foi enviado automaticamente pelo sistema Share2Inspire.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            params={"date": "{{date}}"},
            headers={"Some-Custom-Header": "newsletter-subscription"}
        )
        
        # Enviar o email para o administrador
        logger.info("A enviar notificação de newsletter via Brevo API")
        api_response = api_instance.send_transac_email(admin_email)
        logger.info(f"Email enviado com sucesso. ID da mensagem: {api_response.message_id}")
        
        # Construir o email de confirmação para o utilizador
        user_confirmation = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": user_email, "name": user_name}],
            sender={"email": VERIFIED_SENDER_EMAIL, "name": VERIFIED_SENDER_NAME},
            subject="Confirmação de Subscrição da Newsletter - Share2Inspire",
            html_content=f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    h2 {{ color: #BF9A33; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                    .message {{ background-color: #f9f9f9; padding: 15px; border-left: 4px solid #BF9A33; }}
                    .footer {{ margin-top: 30px; font-size: 12px; color: #777; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Subscrição Confirmada</h2>
                    <p>Olá {user_name},</p>
                    <div class="message">
                        <p>Obrigado por subscrever a nossa newsletter! A partir de agora, receberá as nossas atualizações e novidades diretamente no seu email.</p>
                    </div>
                    <p>Se não solicitou esta subscrição, pode ignorar este email ou responder para nos informar.</p>
                    <div class="footer">
                        <p>Este email foi enviado automaticamente pelo sistema Share2Inspire.</p>
                        <p>© Share2Inspire - Todos os direitos reservados</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            params={"date": "{{date}}"},
            headers={"Some-Custom-Header": "newsletter-confirmation"}
        )
        
        # Enviar o email para o utilizador
        logger.info("A enviar confirmação de newsletter para o utilizador via Brevo API")
        user_response = api_instance.send_transac_email(user_confirmation)
        logger.info(f"Email de confirmação enviado com sucesso. ID da mensagem: {user_response.message_id}")
        
        return jsonify({
            "message": "Subscrição realizada com sucesso!",
            "status": "success",
            "messageId": api_response.message_id
        }), 200
        
    except ApiException as e:
        # Tratamento específico de erros da API Brevo
        error_body = getattr(e, 'body', str(e))
        error_status = getattr(e, 'status', 500)
        logger.error(f"Erro na API Brevo: Status {error_status}, Corpo: {error_body}")
        
        # Mapear códigos de erro comuns para mensagens amigáveis
        error_messages = {
            400: "Dados inválidos no pedido. Verifique os campos e tente novamente.",
            401: "Erro de autenticação com a API Brevo. Verifique a chave API.",
            403: "Acesso negado à API Brevo. Verifique as permissões da chave API.",
            429: "Limite de envios excedido. Tente novamente mais tarde.",
            500: "Erro no servidor Brevo. Tente novamente mais tarde."
        }
        
        user_message = error_messages.get(error_status, "Ocorreu um erro ao processar a subscrição. Tente novamente mais tarde.")
        
        return jsonify({
            "error": user_message,
            "status": "error",
            "details": str(error_body) if os.getenv("FLASK_ENV") == "development" else None
        }), error_status
        
    except Exception as e:
        # Tratamento genérico de outros erros
        logger.exception(f"Erro inesperado ao processar subscrição de newsletter: {str(e)}")
        
        return jsonify({
            "error": "Ocorreu um erro inesperado ao processar a sua subscrição. Por favor, tente novamente mais tarde.",
            "status": "error"
        }), 500

