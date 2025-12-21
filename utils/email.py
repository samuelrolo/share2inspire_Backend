import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from utils.secrets import get_secret

def get_brevo_api():
    configuration = sib_api_v3_sdk.Configuration()
    api_key = get_secret("BREVO_API_KEY")
    configuration.api_key["api-key"] = api_key
    return sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

def send_email_with_attachments(to_email, to_name, subject, html_content, attachments=None):
    """
    Sends an email via Brevo with optional attachments.
    attachments: list of dicts with 'content' (base64) and 'name'.
    """
    try:
        api_instance = get_brevo_api()
        sender_email = os.getenv("BREVO_SENDER_EMAIL", "srshare2inspire@gmail.com")
        sender_name = os.getenv("BREVO_SENDER_NAME", "Share2Inspire")
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": to_email, "name": to_name}],
            bcc=[{"email": "srshare2inspire@gmail.com", "name": "Admin Share2Inspire"}],
            sender={"email": sender_email, "name": sender_name},
            subject=subject,
            html_content=html_content,
            attachment=attachments
        )
        
        api_instance.send_transac_email(send_smtp_email)
        return True, "Email enviado com sucesso"
    except ApiException as e:
        return False, f"Erro Brevo: {str(e)}"
    except Exception as e:
        return False, f"Erro inesperado: {str(e)}"

def get_premium_wrapper(content_body, button_text=None, button_link=None, support_text=None):
    """
    Wraps content in the premium Share2Inspire brand layout.
    """
    button_html = ""
    if button_text and button_link:
        button_html = f"""
        <table border="0" cellspacing="0" cellpadding="0" style="margin-top: 24px; margin-bottom: 24px;">
            <tr>
                <td align="center" style="border-radius: 999px;" bgcolor="#BF9A33">
                    <a href="{button_link}" target="_blank" style="font-size: 16px; font-family: 'Poppins', Helvetica, Arial, sans-serif; color: #ffffff; text-decoration: none; padding: 14px 28px; border-radius: 999px; border: 1px solid #BF9A33; display: inline-block; font-weight: 600;">
                        {button_text}
                    </a>
                </td>
            </tr>
        </table>
        """

    support_html = ""
    if support_text:
        support_html = f'<p style="font-size: 13px; color: #777; margin-top: 10px;">{support_text}</p>'

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            @media only screen and (max-width: 600px) {{
                .logo {{ width: 140px !important; }}
                .container {{ margin: 0 16px !important; }}
            }}
        </style>
    </head>
    <body style="margin: 0; padding: 0; background-color: #f4f4f4; font-family: 'Poppins', Helvetica, Arial, sans-serif;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f4f4;">
            <tr>
                <td align="center" style="padding: 24px 0;">
                    <img src="https://share2inspire.pt/images/logo.png" class="logo" width="180" style="display: block; border: 0;" alt="Share2Inspire">
                </td>
            </tr>
            <tr>
                <td align="center">
                    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; overflow: hidden; margin-bottom: 40px;">
                        <tr>
                            <td style="padding: 40px 32px; color: #444; font-size: 16px; line-height: 24px;">
                                {content_body}
                                {button_html}
                                {support_html}
                                <p style="margin-top: 32px; font-size: 14px; color: #666;">
                                    Com estima,<br>
                                    <strong>Equipa Share2Inspire</strong><br>
                                    <a href="https://share2inspire.pt" style="color: #BF9A33; text-decoration: none;">www.share2inspire.pt</a>
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background-color: #212529; padding: 32px; text-align: center;">
                                <p style="font-size: 14px; color: #BF9A33; margin: 0 0 16px; font-weight: 600;">Share2Inspire - Career Excellence</p>
                                <p style="font-size: 12px; line-height: 18px; color: #cccccc; margin: 0;">
                                    Lisboa, Portugal | srshare2inspire@gmail.com<br>
                                    Copyright © 2025 Share2Inspire
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

def get_email_template_1(name, payment_link):
    """Email 1. Envio de link de pagamento, Kickstart Pro"""
    body = f"""
    <p>Olá {name},</p>
    <p>Recebemos o teu pedido para o Kickstart Pro.</p>
    <p>Para confirmar a sessão, pedimos que concluas o pagamento através do link MB Way abaixo. O pagamento é processado de forma segura através da Ifthenpay.</p>
    <p>Assim que o pagamento for confirmado, recebes um novo email com a confirmação da sessão e os respetivos detalhes.</p>
    """
    return get_premium_wrapper(body, "Pagar com MB Way", payment_link, "Este link é individual e válido por tempo limitado.")

def get_email_template_2(name, payment_link):
    """Email 2. Envio de link de pagamento, Revisão Profissional de CV"""
    body = f"""
    <p>Olá {name},</p>
    <p>Recebemos o teu pedido para a Revisão Profissional de CV.</p>
    <p>Para iniciar o processo, pedimos que concluas o pagamento através do link MB Way abaixo. O pagamento é processado de forma segura através da Ifthenpay.</p>
    <p>Após confirmação do pagamento, receberás um novo email com os próximos passos e, se necessário, pedidos de informação adicional.</p>
    """
    return get_premium_wrapper(body, "Pagar com MB Way", payment_link, "O serviço inicia apenas após confirmação do pagamento.")

def get_email_template_3(name, payment_link):
    """Email 3. Envio de link de pagamento, CV Analyzer"""
    body = f"""
    <p>Olá {name},</p>
    <p>A análise inicial do teu CV está concluída.</p>
    <p>Para receberes o Relatório Completo de Análise de CV em PDF, pedimos que concluas o pagamento através do link MB Way abaixo. O pagamento é processado de forma segura através da Ifthenpay.</p>
    <p>Após confirmação do pagamento, o relatório será gerado e enviado automaticamente por email.</p>
    """
    return get_premium_wrapper(body, "Pagar e receber relatório", payment_link, "O relatório inclui a análise aprofundada e o CV submetido em anexo.")

def get_email_template_4(name):
    """Email 4. Confirmação de pagamento, todos os serviços"""
    body = f"""
    <p>Olá {name},</p>
    <p>Confirmamos a receção do teu pagamento.</p>
    <p>Dependendo do serviço solicitado, os próximos passos são os seguintes:</p>
    
    <div style="margin-top: 24px;">
        <p><strong>Kickstart Pro</strong><br>
        Receberás em breve os detalhes da sessão e o respetivo link de acesso.</p>
        
        <p><strong>Revisão Profissional de CV</strong><br>
        O processo de elaboração do teu CV foi iniciado. Entraremos em contacto caso seja necessária informação adicional.</p>
        
        <p><strong>CV Analyzer</strong><br>
        O Relatório Completo de Análise de CV em PDF será enviado automaticamente por email.</p>
    </div>
    
    <p style="margin-top: 24px;">Obrigado pela confiança.</p>
    """
    return get_premium_wrapper(body)
