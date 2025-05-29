# Função para enviar email de confirmação de reserva
import os
import json
import logging
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da API Brevo (Sendinblue)
configuration = sib_api_v3_sdk.Configuration()
api_key = os.getenv("BREVO_API_KEY")
configuration.api_key["api-key"] = api_key

# Email do remetente verificado na Brevo
VERIFIED_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL", "srshare2inspire@gmail.com")
VERIFIED_SENDER_NAME = os.getenv("BREVO_SENDER_NAME", "Share2Inspire")

# Email do destinatário (admin)
ADMIN_EMAIL = "srshare2inspire@gmail.com"
ADMIN_NAME = "Share2Inspire Admin"

api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

def send_booking_confirmation_email(payment_data):
    """
    Envia email de confirmação de reserva após o pagamento
    
    Args:
        payment_data (dict): Dados do pagamento e da reserva
    
    Returns:
        bool: True se o email foi enviado com sucesso, False caso contrário
    """
    try:
        # Extrair dados do pagamento
        customer_name = payment_data.get("customerName", "Cliente")
        customer_email = payment_data.get("customerEmail")
        customer_phone = payment_data.get("customerPhone", "Não fornecido")
        order_id = payment_data.get("orderId", "")
        method = payment_data.get("method", "")
        amount = payment_data.get("amount", 0)
        entity = payment_data.get("entity", "")
        reference = payment_data.get("reference", "")
        description = payment_data.get("description", "")
        appointment_date = payment_data.get("appointmentDate", "")
        appointment_time = payment_data.get("appointmentTime", "")
        
        # Verificar se o email do cliente está disponível
        if not customer_email:
            logger.error(f"Email do cliente não fornecido para o pedido {order_id}")
            return False
        
        # Determinar o tipo de pagamento para personalizar o email
        payment_method_name = get_payment_method_name(method)
        
        # Construir o conteúdo do email com base no método de pagamento
        payment_details_html = ""
        if method == "multibanco" or method == "mb":
            payment_details_html = f"""
            <div style="background-color: #f5f5f5; padding: 15px; margin: 15px 0; border-radius: 5px;">
                <h3 style="color: #0066cc; margin-top: 0;">Detalhes de Pagamento Multibanco</h3>
                <p><strong>Entidade:</strong> {entity}</p>
                <p><strong>Referência:</strong> {reference}</p>
                <p><strong>Valor:</strong> {amount}€</p>
                <p><em>A referência é válida por 48 horas. Por favor efetue o pagamento o mais brevemente possível para confirmar a sua marcação.</em></p>
            </div>
            """
        elif method == "mbway":
            payment_details_html = f"""
            <div style="background-color: #f5f5f5; padding: 15px; margin: 15px 0; border-radius: 5px;">
                <h3 style="color: #0066cc; margin-top: 0;">Detalhes de Pagamento MB WAY</h3>
                <p>Foi enviado um pedido de pagamento para o seu telemóvel através do MB WAY.</p>
                <p><strong>Número:</strong> {customer_phone}</p>
                <p><strong>Valor:</strong> {amount}€</p>
                <p><strong>Referência:</strong> {reference}</p>
                <p><em>Por favor verifique a aplicação MB WAY no seu telemóvel e aceite o pagamento para confirmar a sua marcação.</em></p>
            </div>
            """
        elif method == "payshop":
            payment_details_html = f"""
            <div style="background-color: #f5f5f5; padding: 15px; margin: 15px 0; border-radius: 5px;">
                <h3 style="color: #0066cc; margin-top: 0;">Detalhes de Pagamento Payshop</h3>
                <p><strong>Referência:</strong> {reference}</p>
                <p><strong>Valor:</strong> {amount}€</p>
                <p><em>Pode efetuar o pagamento em qualquer agente Payshop ou CTT. A referência é válida por 30 dias.</em></p>
            </div>
            """
        
        # Construir o email para o cliente
        client_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": customer_email, "name": customer_name}],
            sender={"email": VERIFIED_SENDER_EMAIL, "name": VERIFIED_SENDER_NAME},
            subject=f"Confirmação de Marcação - Share2Inspire",
            html_content=f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    h2 {{ color: #BF9A33; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                    .booking-details {{ background-color: #f9f9f9; padding: 15px; border-left: 4px solid #BF9A33; margin: 15px 0; }}
                    .footer {{ margin-top: 30px; font-size: 12px; color: #777; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Confirmação de Marcação</h2>
                    <p>Olá {customer_name},</p>
                    <p>Obrigado pela sua marcação. Abaixo estão os detalhes da sua sessão:</p>
                    
                    <div class="booking-details">
                        <p><strong>Serviço:</strong> {description.split('#')[0] if '#' in description else description}</p>
                        <p><strong>Data:</strong> {appointment_date}</p>
                        <p><strong>Hora:</strong> {appointment_time}</p>
                        <p><strong>Referência:</strong> {order_id}</p>
                    </div>
                    
                    {payment_details_html}
                    
                    <p>Se tiver alguma dúvida ou precisar de alterar a sua marcação, por favor contacte-nos através do email <a href="mailto:srshare2inspire@gmail.com">srshare2inspire@gmail.com</a> ou telefone <a href="tel:+351910000000">+351 910 000 000</a>.</p>
                    
                    <p>Aguardamos a sua visita!</p>
                    <p>Cumprimentos,<br>Equipa Share2Inspire</p>
                    
                    <div class="footer">
                        <p>Este email foi enviado automaticamente pelo sistema Share2Inspire.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            # Adicionar opções de rastreamento
            params={"date": "{{date}}"},
            headers={"Some-Custom-Header": "booking-confirmation"}
        )
        
        # Enviar o email para o cliente
        logger.info(f"A enviar email de confirmação de reserva para {customer_email}")
        client_response = api_instance.send_transac_email(client_email)
        logger.info(f"Email enviado com sucesso para o cliente. ID da mensagem: {client_response.message_id}")
        
        # Construir o email para o administrador
        admin_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": ADMIN_EMAIL, "name": ADMIN_NAME}],
            sender={"email": VERIFIED_SENDER_EMAIL, "name": VERIFIED_SENDER_NAME},
            subject=f"Nova Marcação: {description.split('#')[0] if '#' in description else description}",
            html_content=f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    h2 {{ color: #BF9A33; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                    .booking-details {{ background-color: #f9f9f9; padding: 15px; border-left: 4px solid #BF9A33; margin: 15px 0; }}
                    .payment-details {{ background-color: #f5f5f5; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                    .footer {{ margin-top: 30px; font-size: 12px; color: #777; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Nova Marcação Recebida</h2>
                    <p>Foi recebida uma nova marcação com os seguintes detalhes:</p>
                    
                    <div class="booking-details">
                        <p><strong>Cliente:</strong> {customer_name}</p>
                        <p><strong>Email:</strong> {customer_email}</p>
                        <p><strong>Telefone:</strong> {customer_phone}</p>
                        <p><strong>Serviço:</strong> {description.split('#')[0] if '#' in description else description}</p>
                        <p><strong>Data:</strong> {appointment_date}</p>
                        <p><strong>Hora:</strong> {appointment_time}</p>
                        <p><strong>Referência:</strong> {order_id}</p>
                    </div>
                    
                    <div class="payment-details">
                        <h3 style="color: #0066cc; margin-top: 0;">Detalhes de Pagamento</h3>
                        <p><strong>Método:</strong> {payment_method_name}</p>
                        <p><strong>Valor:</strong> {amount}€</p>
                        <p><strong>Estado:</strong> Pendente</p>
                        <p><strong>Referência:</strong> {reference}</p>
                        {f"<p><strong>Entidade:</strong> {entity}</p>" if entity else ""}
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
            headers={"Some-Custom-Header": "booking-notification-admin"}
        )
        
        # Enviar o email para o administrador
        logger.info(f"A enviar notificação de nova reserva para o administrador")
        admin_response = api_instance.send_transac_email(admin_email)
        logger.info(f"Email enviado com sucesso para o administrador. ID da mensagem: {admin_response.message_id}")
        
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

def get_payment_method_name(method):
    """
    Obtém o nome amigável do método de pagamento
    
    Args:
        method (str): Código do método de pagamento
        
    Returns:
        str: Nome amigável do método de pagamento
    """
    method_names = {
        "mb": "Multibanco",
        "multibanco": "Multibanco",
        "mbway": "MB WAY",
        "payshop": "Payshop"
    }
    
    return method_names.get(method.lower(), "Desconhecido")
