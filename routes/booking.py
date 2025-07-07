from flask import Blueprint, request, jsonify
import os
import json
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

booking_bp = Blueprint("booking", __name__, url_prefix="/api/booking")

# Configuração da API Brevo (Sendinblue)
configuration = sib_api_v3_sdk.Configuration()
api_key = os.getenv("BREVO_API_KEY")
configuration.api_key["api-key"] = api_key

# Verificar se a chave API foi carregada
if not configuration.api_key["api-key"]:
    print("ALERTA: A variável de ambiente BREVO_API_KEY não está definida!")
else:
    print(f"BREVO_API_KEY carregada com sucesso: {api_key[:3]}{'*' * (len(api_key) - 3)}")

api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

@booking_bp.route("/schedule", methods=["POST"])
def schedule_appointment():
    try:
        print("Endpoint /api/booking/schedule chamado com método POST")
        data = request.get_json()
        print(f"Dados recebidos: {json.dumps(data, indent=2)}")
        
        if not data:
            print("Erro: Nenhum dado recebido no corpo da requisição")
            return jsonify({"error": "Nenhum dado recebido"}), 400

        # Extrair dados do pedido
        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        service_type = data.get("serviceType")
        date = data.get("date")
        message = data.get("message", "")

        print(f"Dados extraídos: nome={name}, email={email}, telefone={phone}, serviço={service_type}, data={date}")

        # Validar dados essenciais
        if not all([name, email, phone, service_type, date]):
            missing = []
            if not name: missing.append("name")
            if not email: missing.append("email")
            if not phone: missing.append("phone")
            if not service_type: missing.append("serviceType")
            if not date: missing.append("date")
            
            print(f"Erro: Dados incompletos para agendamento. Campos em falta: {', '.join(missing)}")
            return jsonify({"error": f"Dados incompletos para agendamento. Campos em falta: {', '.join(missing)}"}), 400

        # Construir o email - E-MAIL CORRIGIDO
        print("Construindo email para envio via Brevo...")
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": "share2inspire@gmail.com", "name": "Share2Inspire Admin"}],
            sender={"email": os.getenv("BREVO_SENDER_EMAIL", "noreply@share2inspire.pt"), "name": "Sistema de Agendamento"},
            subject=f"Novo Agendamento - {service_type}",
            html_content=f"""
            <html><body>
                <h2>Novo Agendamento Recebido</h2>
                <p><strong>Nome:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Telefone:</strong> {phone}</p>
                <p><strong>Tipo de Serviço:</strong> {service_type}</p>
                <p><strong>Data Pretendida:</strong> {date}</p>
                <p><strong>Mensagem:</strong></p>
                <p>{message}</p>
            </body></html>
            """,
            reply_to={"email": email, "name": name}
        )

        try:
            print("Tentando enviar email via API Brevo...")
            api_response = api_instance.send_transac_email(send_smtp_email)
            print(f"Email de agendamento enviado via Brevo. Resposta: {api_response}")
            return jsonify({"message": "Agendamento recebido com sucesso! Entraremos em contacto brevemente."}), 200
        except ApiException as e:
            print(f"Erro ao enviar email de agendamento via Brevo: {e}")
            error_body = e.body
            error_status = e.status
            print(f"Status: {error_status}, Body: {error_body}")
            
            # Verificar se é um erro de autenticação
            if error_status == 401:
                print("ERRO DE AUTENTICAÇÃO: Verifique se a chave da API Brevo está correta")
            
            return jsonify({
                "error": "Ocorreu um erro de comunicação ao tentar realizar o agendamento. Verifique a sua ligação à internet e tente novamente.", 
                "details": str(e),
                "status": error_status
            }), 500
        except Exception as e:
            print(f"Erro inesperado ao processar agendamento: {e}")
            return jsonify({"error": "Ocorreu um erro inesperado.", "details": str(e)}), 500
    except Exception as e:
        print(f"Erro global no endpoint /schedule: {e}")
        return jsonify({"error": "Ocorreu um erro no servidor.", "details": str(e)}), 500

@booking_bp.route("/consultation", methods=["POST"])
def request_consultation():
    try:
        print("Endpoint /api/booking/consultation chamado com método POST")
        data = request.get_json()
        print(f"Dados recebidos: {json.dumps(data, indent=2)}")
        
        if not data:
            print("Erro: Nenhum dado recebido no corpo da requisição")
            return jsonify({"error": "Nenhum dado recebido"}), 400

        # Extrair dados do pedido
        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        topic = data.get("topic")
        message = data.get("message", "")

        print(f"Dados extraídos: nome={name}, email={email}, telefone={phone}, tópico={topic}")

        # Validar dados essenciais
        if not all([name, email, phone, topic]):
            missing = []
            if not name: missing.append("name")
            if not email: missing.append("email")
            if not phone: missing.append("phone")
            if not topic: missing.append("topic")
            
            print(f"Erro: Dados incompletos para pedido de consultoria. Campos em falta: {', '.join(missing)}")
            return jsonify({"error": f"Dados incompletos para pedido de consultoria. Campos em falta: {', '.join(missing)}"}), 400

        # Construir o email - E-MAIL CORRIGIDO
        print("Construindo email para envio via Brevo...")
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": "share2inspire@gmail.com", "name": "Share2Inspire Admin"}],
            sender={"email": os.getenv("BREVO_SENDER_EMAIL", "noreply@share2inspire.pt"), "name": "Sistema de Consultoria"},
            subject=f"Novo Pedido de Consultoria - {topic}",
            html_content=f"""
            <html><body>
                <h2>Novo Pedido de Consultoria Recebido</h2>
                <p><strong>Nome:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Telefone:</strong> {phone}</p>
                <p><strong>Tópico:</strong> {topic}</p>
                <p><strong>Mensagem:</strong></p>
                <p>{message}</p>
            </body></html>
            """,
            reply_to={"email": email, "name": name}
        )

        try:
            print("Tentando enviar email via API Brevo...")
            api_response = api_instance.send_transac_email(send_smtp_email)
            print(f"Email de pedido de consultoria enviado via Brevo. Resposta: {api_response}")
            return jsonify({"message": "Pedido de consultoria recebido com sucesso! Entraremos em contacto brevemente."}), 200
        except ApiException as e:
            print(f"Erro ao enviar email de pedido de consultoria via Brevo: {e}")
            error_body = e.body
            error_status = e.status
            print(f"Status: {error_status}, Body: {error_body}")
            
            # Verificar se é um erro de autenticação
            if error_status == 401:
                print("ERRO DE AUTENTICAÇÃO: Verifique se a chave da API Brevo está correta")
            
            return jsonify({
                "error": "Ocorreu um erro de comunicação ao tentar enviar o pedido de consultoria. Verifique a sua ligação à internet e tente novamente.", 
                "details": str(e),
                "status": error_status
            }), 500
        except Exception as e:
            print(f"Erro inesperado ao processar pedido de consultoria: {e}")
            return jsonify({"error": "Ocorreu um erro inesperado.", "details": str(e)}), 500
    except Exception as e:
        print(f"Erro global no endpoint /consultation: {e}")
        return jsonify({"error": "Ocorreu um erro no servidor.", "details": str(e)}), 500

@booking_bp.route("/content", methods=["POST"])
def request_content():
    try:
        print("Endpoint /api/booking/content chamado com método POST")
        data = request.get_json()
        print(f"Dados recebidos: {json.dumps(data, indent=2)}")
        
        if not data:
            print("Erro: Nenhum dado recebido no corpo da requisição")
            return jsonify({"error": "Nenhum dado recebido"}), 400

        # Extrair dados do pedido
        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        content_type = data.get("contentType")
        description = data.get("description", "")

        print(f"Dados extraídos: nome={name}, email={email}, telefone={phone}, tipo de conteúdo={content_type}")

        # Validar dados essenciais
        if not all([name, email, phone, content_type]):
            missing = []
            if not name: missing.append("name")
            if not email: missing.append("email")
            if not phone: missing.append("phone")
            if not content_type: missing.append("contentType")
            
            print(f"Erro: Dados incompletos para pedido de criação de conteúdo. Campos em falta: {', '.join(missing)}")
            return jsonify({"error": f"Dados incompletos para pedido de criação de conteúdo. Campos em falta: {', '.join(missing)}"}), 400

        # Construir o email - E-MAIL CORRIGIDO
        print("Construindo email para envio via Brevo...")
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": "share2inspire@gmail.com", "name": "Share2Inspire Admin"}],
            sender={"email": os.getenv("BREVO_SENDER_EMAIL", "noreply@share2inspire.pt"), "name": "Sistema de Criação de Conteúdos"},
            subject=f"Novo Pedido de Criação de Conteúdo - {content_type}",
            html_content=f"""
            <html><body>
                <h2>Novo Pedido de Criação de Conteúdo Recebido</h2>
                <p><strong>Nome:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Telefone:</strong> {phone}</p>
                <p><strong>Tipo de Conteúdo:</strong> {content_type}</p>
                <p><strong>Descrição:</strong></p>
                <p>{description}</p>
            </body></html>
            """,
            reply_to={"email": email, "name": name}
        )

        try:
            print("Tentando enviar email via API Brevo...")
            api_response = api_instance.send_transac_email(send_smtp_email)
            print(f"Email de pedido de criação de conteúdo enviado via Brevo. Resposta: {api_response}")
            return jsonify({"message": "Pedido de criação de conteúdo recebido com sucesso! Entraremos em contacto brevemente."}), 200
        except ApiException as e:
            print(f"Erro ao enviar email de pedido de criação de conteúdo via Brevo: {e}")
            error_body = e.body
            error_status = e.status
            print(f"Status: {error_status}, Body: {error_body}")
            
            # Verificar se é um erro de autenticação
            if error_status == 401:
                print("ERRO DE AUTENTICAÇÃO: Verifique se a chave da API Brevo está correta")
            
            return jsonify({
                "error": "Ocorreu um erro de comunicação ao tentar enviar o pedido de criação de conteúdo. Verifique a sua ligação à internet e tente novamente.", 
                "details": str(e),
                "status": error_status
            }), 500
        except Exception as e:
            print(f"Erro inesperado ao processar pedido de criação de conteúdo: {e}")
            return jsonify({"error": "Ocorreu um erro inesperado.", "details": str(e)}), 500
    except Exception as e:
        print(f"Erro global no endpoint /content: {e}")
        return jsonify({"error": "Ocorreu um erro no servidor.", "details": str(e)}), 500

