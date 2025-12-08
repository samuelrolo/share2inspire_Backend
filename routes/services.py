from flask import Blueprint, request, jsonify
import os
import json
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

services_bp = Blueprint("services", __name__, url_prefix="/api/services")

# Configuração da API Brevo (Sendinblue)
configuration = sib_api_v3_sdk.Configuration()
api_key = os.getenv("BREVO_API_KEY")
configuration.api_key["api-key"] = api_key

api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

@services_bp.route("/cv-review", methods=["POST"])
def request_cv_review():
    try:
        print("Endpoint /api/services/cv-review chamado com método POST")
        
        # Verificar se é um request com arquivo (multipart/form-data)
        if not request.content_type or 'multipart/form-data' not in request.content_type:
             # Fallback para JSON (caso antigo ou teste)
             data = request.get_json()
             if not data:
                return jsonify({"error": "Formato inválido. Esperado multipart/form-data ou JSON"}), 400
        else:
            # Processar multipart/form-data
            data = request.form
            
        print(f"Dados recebidos: {data}")

        # Extrair dados do pedido
        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        experience = data.get("experience")
        objectives = data.get("objectives")
        
        # O CV pode vir como link (JSON) ou arquivo (FormData)
        cv_link = data.get("cv_link") 
        cv_file = request.files.get("cv_file") if request.files else None

        print(f"Dados extraídos: nome={name}, email={email}, telefone={phone}")

        # Validar dados essenciais
        if not all([name, email, objectives]) or (not cv_link and not cv_file):
            missing = []
            if not name: missing.append("name")
            if not email: missing.append("email")
            if not objectives: missing.append("objectives")
            if not cv_link and not cv_file: missing.append("cv_file/cv_link")
            
            print(f"Erro: Dados incompletos para revisão de CV. Campos em falta: {', '.join(missing)}")
            return jsonify({"error": f"Dados incompletos para revisão de CV. Campos em falta: {', '.join(missing)}"}), 400

        # Preparar anexo se houver arquivo
        attachment = None
        if cv_file:
            import base64
            file_content = cv_file.read()
            encoded_content = base64.b64encode(file_content).decode('utf-8')
            attachment = [{
                "content": encoded_content,
                "name": cv_file.filename
            }]
            cv_info = f"Anexo: {cv_file.filename}"
        else:
            cv_info = f"Link: <a href='{cv_link}'>{cv_link}</a>"

        # Construir o email
        print("Construindo email para envio via Brevo...")
        
        email_content = f"""
            <html><body>
                <h2>Novo Pedido de Revisão de CV Recebido</h2>
                <p><strong>Nome:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Telefone:</strong> {phone}</p>
                <p><strong>CV:</strong> {cv_info}</p>
                <p><strong>Experiência:</strong> {experience}</p>
                <p><strong>Objetivos:</strong></p>
                <p>{objectives}</p>
            </body></html>
            """

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": "srshare2inspire@gmail.com", "name": "Share2Inspire Admin"}],
            sender={"email": os.getenv("BREVO_SENDER_EMAIL", "noreply@share2inspire.pt"), "name": "Sistema de Serviços"},
            subject=f"Novo Pedido de Revisão de CV - {name}",
            html_content=email_content,
            reply_to={"email": email, "name": name},
            attachment=attachment if attachment else None
        )

        try:
            print("Tentando enviar email via API Brevo...")
            api_response = api_instance.send_transac_email(send_smtp_email)
            print(f"Email de revisão de CV enviado via Brevo. Resposta: {api_response}")
            return jsonify({"message": "Pedido de revisão de CV recebido com sucesso! Entraremos em contacto brevemente."}), 200
        except ApiException as e:
            print(f"Erro ao enviar email de revisão de CV via Brevo: {e}")
            error_body = e.body
            error_status = e.status
            print(f"Status: {error_status}, Body: {error_body}")
            
            return jsonify({
                "error": "Ocorreu um erro de comunicação ao tentar enviar o pedido. Verifique a sua ligação à internet e tente novamente.", 
                "details": str(e),
                "status": error_status
            }), 500
        except Exception as e:
            print(f"Erro inesperado ao processar pedido de revisão de CV: {e}")
            return jsonify({"error": "Ocorreu um erro inesperado.", "details": str(e)}), 500
    except Exception as e:
        print(f"Erro global no endpoint /cv-review: {e}")
        return jsonify({"error": "Ocorreu um erro no servidor.", "details": str(e)}), 500

@services_bp.route("/kickstart-email", methods=["POST"])
def send_kickstart_email():
    try:
        data = request.get_json()
        print(f"Dados recebidos para email Kickstart: {data}")
        
        if not data:
            return jsonify({"success": False, "error": "Dados não recebidos"}), 400
            
        email = data.get('email')
        name = data.get('name')
        
        if not email or not name:
            return jsonify({"success": False, "error": "Email e Nome obrigatórios"}), 400
            
        # Construir o email
        subject = "Confirmação - Kickstart Pro Share2Inspire"
        html_content = f"""
        <html><body>
            <h2>Obrigado pelo seu interesse no Kickstart Pro!</h2>
            <p>Olá {name},</p>
            <p>Recebemos a sua marcação para o Kickstart Pro. Entraremos em contacto brevemente.</p>
            <p><strong>Detalhes:</strong></p>
            <ul>
                <li>Nome: {name}</li>
                <li>Email: {email}</li>
                <li>Data: {data.get('date', 'A definir')}</li>
                <li>Duração: {data.get('duration', '30 minutos')}</li>
            </ul>
            <p>Cumprimentos,<br>Equipa Share2Inspire</p>
        </body></html>
        """
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": email, "name": name}],
            sender={"email": os.getenv("BREVO_SENDER_EMAIL", "noreply@share2inspire.pt"), "name": "Share2Inspire"},
            subject=subject,
            html_content=html_content
        )
        
        try:
            api_instance.send_transac_email(send_smtp_email)
            return jsonify({"success": True, "message": "Email enviado com sucesso"})
        except ApiException as e:
            print(f"Erro Brevo: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
            
    except Exception as e:
        print(f"Erro no endpoint kickstart-email: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
