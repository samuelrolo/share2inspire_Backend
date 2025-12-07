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
        data = request.get_json()
        print(f"Dados recebidos: {json.dumps(data, indent=2)}")
        
        if not data:
            print("Erro: Nenhum dado recebido no corpo da requisição")
            return jsonify({"error": "Nenhum dado recebido"}), 400

        # Extrair dados do pedido
        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        cv_link = data.get("cv_link")
        experience = data.get("experience")
        objectives = data.get("objectives")

        print(f"Dados extraídos: nome={name}, email={email}, telefone={phone}, cv_link={cv_link}")

        # Validar dados essenciais
        if not all([name, email, cv_link, objectives]):
            missing = []
            if not name: missing.append("name")
            if not email: missing.append("email")
            if not cv_link: missing.append("cv_link")
            if not objectives: missing.append("objectives")
            
            print(f"Erro: Dados incompletos para revisão de CV. Campos em falta: {', '.join(missing)}")
            return jsonify({"error": f"Dados incompletos para revisão de CV. Campos em falta: {', '.join(missing)}"}), 400

        # Construir o email
        print("Construindo email para envio via Brevo...")
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": "srshare2inspire@gmail.com", "name": "Share2Inspire Admin"}],
            sender={"email": os.getenv("BREVO_SENDER_EMAIL", "noreply@share2inspire.pt"), "name": "Sistema de Serviços"},
            subject=f"Novo Pedido de Revisão de CV - {name}",
            html_content=f"""
            <html><body>
                <h2>Novo Pedido de Revisão de CV Recebido</h2>
                <p><strong>Nome:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Telefone:</strong> {phone}</p>
                <p><strong>Link para CV:</strong> <a href="{cv_link}">{cv_link}</a></p>
                <p><strong>Experiência:</strong> {experience}</p>
                <p><strong>Objetivos:</strong></p>
                <p>{objectives}</p>
            </body></html>
            """,
            reply_to={"email": email, "name": name}
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
