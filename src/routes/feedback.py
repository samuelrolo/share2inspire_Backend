# /home/ubuntu/share2inspire_backend/src/routes/feedback.py

import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv

# Carregar variáveis de ambiente do ficheiro .env
load_dotenv()

feedback_bp = Blueprint("feedback", __name__, url_prefix="/api/feedback")

# Configuração da API Brevo (Sendinblue)
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key["api-key"] = os.getenv("BREVO_API_KEY")

# Verificar se a chave API foi carregada
if not configuration.api_key["api-key"]:
    print("ALERTA: A variável de ambiente BREVO_API_KEY não está definida!")
    # Considerar lançar um erro ou logar de forma mais robusta

api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

@feedback_bp.route("/submit", methods=["POST"])
def submit_feedback():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Nenhum dado recebido"}), 400

    rating = data.get("rating")
    message = data.get("message")
    # Poderia adicionar mais campos se o formulário os enviar (ex: nome, email do utilizador)

    if not rating or not message:
        return jsonify({"error": "Campos 'rating' e 'message' são obrigatórios"}), 400

    # Construir o email
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": "srshare2inspire@gmail.com", "name": "Share2Inspire Admin"}],
        # Idealmente, o remetente deve ser um email verificado no Brevo
        sender={"email": os.getenv("BREVO_SENDER_EMAIL", "noreply@seudominio.com"), "name": "Feedback Share2Inspire"},
        subject="Novo Feedback Recebido - Share2Inspire",
        html_content=f"""
        <html><body>
            <h2>Novo Feedback Recebido</h2>
            <p><strong>Avaliação:</strong> {rating} estrelas</p>
            <p><strong>Mensagem:</strong></p>
            <p>{message}</p>
        </body></html>
        """
        # reply_to={"email": "email_do_utilizador@exemplo.com", "name": "Nome Utilizador"} # Se receber email do utilizador
    )

    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        print("Email de feedback enviado via Brevo. Resposta:", api_response)
        return jsonify({"message": "Feedback enviado com sucesso!"}), 200
    except ApiException as e:
        print(f"Erro ao enviar email de feedback via Brevo: {e}")
        # Log detalhado do erro
        error_body = e.body
        error_status = e.status
        print(f"Status: {error_status}, Body: {error_body}")
        return jsonify({"error": "Ocorreu um erro ao enviar o feedback. Tente novamente mais tarde.", "details": str(e)}), 500
    except Exception as e:
        print(f"Erro inesperado ao enviar feedback: {e}")
        return jsonify({"error": "Ocorreu um erro inesperado.", "details": str(e)}), 500

