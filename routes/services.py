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
        from routes.payment import create_mbway_payment, normalize_payment_data

        print("Endpoint /api/services/cv-review chamado com método POST")
        
        # Verificar se é um request com arquivo (multipart/form-data)
        if not request.content_type or 'multipart/form-data' not in request.content_type:
             data = request.get_json()
             if not data:
                return jsonify({"error": "Formato inválido. Esperado multipart/form-data"}), 400
        else:
            data = request.form
            
        print(f"Dados recebidos: {data}")

        # Extrair dados do pedido
        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        experience = data.get("experience")
        
        # Mapeamento do campo de características/objetivos
        # O formulário envia 'ad_characteristics' como principal campo de texto, mas também pode ter 'objectives'
        ad_characteristics = data.get("ad_characteristics", "")
        objectives = data.get("objectives", "")
        
        # Combinar para email se ambos existirem
        full_context = ""
        if ad_characteristics:
            full_context += f"<p><strong>Características do Anúncio/Vaga:</strong><br>{ad_characteristics}</p>"
        if objectives:
            full_context += f"<p><strong>Objetivos da Revisão:</strong><br>{objectives}</p>"
            
        if not full_context:
             full_context = "<p><em>Nenhum contexto adicional fornecido.</em></p>"

        # Novos campos adicionados pelo utilizador
        current_role = data.get("current_role", "N/A")
        sector = data.get("sector", "N/A")
        linkedin_url = data.get("linkedin_url", "N/A")
        
        # O CV pode vir como link (JSON) ou arquivo (FormData)
        cv_link = data.get("cv_link") 
        cv_file = request.files.get("cv_file") if request.files else None
        
        print(f"Dados extraídos: nome={name}, email={email}, telefone={phone}")

        # Validar dados essenciais
        if not all([name, email, phone]):
             return jsonify({"success": False, "error": "Dados obrigatórios em falta (Nome, Email, Telefone)"}), 400

        # >>> 1. Iniciar Pagamento MB WAY (15.00€) <<<
        payment_data = {
            "amount": "15.00",
            "orderId": data.get("orderId", f"CV-{name.replace(' ', '')}"),
            "phone": phone,
            "email": email,
            "description": f"Revisao CV - {name}"
        }
        
        # Normalizar e criar pagamento
        print(f"Iniciando pagamento MB WAY para {name}...")
        normalized_payment = normalize_payment_data(payment_data)
        payment_result = create_mbway_payment(normalized_payment)
        
        if not payment_result.get('success'):
            print(f"Erro ao criar pagamento: {payment_result.get('error')}")
            # Retornamos erro se pagamento falhar
            return jsonify({"success": False, "error": f"Erro ao iniciar pagamento MB WAY: {payment_result.get('error')}"}), 400

        # >>> 2. Enviar Email com Anexo <<<
        
        # Preparar anexo
        attachment = None
        cv_info = "Nenhum ficheiro enviado"
        
        if cv_file:
            import base64
            file_content = cv_file.read()
            encoded_content = base64.b64encode(file_content).decode('utf-8')
            attachment = [{
                "content": encoded_content,
                "name": cv_file.filename
            }]
            cv_info = f"Anexo: {cv_file.filename}"
        elif cv_link:
            cv_info = f"Link: <a href='{cv_link}'>{cv_link}</a>"

        email_content = f"""
            <html><body>
                <h2>Novo Pedido de Revisão de CV (Pendente Pagamento)</h2>
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <p><strong>Status Pagamento:</strong> Iniciado (MB WAY 15.00€)</p>
                    <p><strong>Referência Pedido:</strong> {payment_data['orderId']}</p>
                </div>
                
                <h3>Dados do Candidato</h3>
                <ul>
                    <li><strong>Nome:</strong> {name}</li>
                    <li><strong>Email:</strong> {email}</li>
                    <li><strong>Telefone:</strong> {phone}</li>
                    <li><strong>LinkedIn:</strong> {linkedin_url}</li>
                    <li><strong>Função Atual:</strong> {current_role}</li>
                    <li><strong>Setor:</strong> {sector}</li>
                    <li><strong>Experiência:</strong> {experience}</li>
                </ul>

                <h3>Contexto</h3>
                {full_context}
                
                <hr>
                <p><strong>CV:</strong> {cv_info}</p>
            </body></html>
            """

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": "srshare2inspire@gmail.com", "name": "Share2Inspire Admin"}],
            sender={"email": os.getenv("BREVO_SENDER_EMAIL", "noreply@share2inspire.pt"), "name": "Sistema de Serviços"},
            subject=f"Revisão CV - {name} (Aguardar Pagamento)",
            html_content=email_content,
            reply_to={"email": email, "name": name},
            attachment=attachment if attachment else None
        )

        try:
            api_instance.send_transac_email(send_smtp_email)
            print("Email enviado com sucesso.")
            
            # Sucesso total
            return jsonify({
                "success": True, 
                "message": "Isso", 
                "payment": payment_result
            }), 200
            
        except ApiException as e:
            print(f"Erro Brevo: {e}")
            # Se o email falhar, mas o pagamento foi iniciado, avisamos o user
            return jsonify({
                "success": True, 
                "message": "Pagamento iniciado, mas erro ao enviar email de confirmação. Contacte o suporte.",
                "payment": payment_result,
                "warning": str(e)
            }), 200

    except Exception as e:
        print(f"Erro global no endpoint /cv-review: {e}")
        return jsonify({"success": False, "error": "Erro interno do servidor", "details": str(e)}), 500

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

@services_bp.route("/analyze-cv", methods=["POST"])
def analyze_cv():
    try:
        from utils.analysis import CVAnalyzer
        
        print("Endpoint /api/services/analyze-cv chamado")
        
        # Validar ficheiro
        if 'cv_file' not in request.files:
            return jsonify({"success": False, "error": "Ficheiro não encontrado"}), 400
            
        file = request.files['cv_file']
        if file.filename == '':
            return jsonify({"success": False, "error": "Nome de ficheiro inválido"}), 400

        # Validar outros dados
        data = request.form
        role = data.get('current_role', '')
        experience = data.get('experience', '')
        
        # Executar análise
        analyzer = CVAnalyzer()
        report = analyzer.analyze(file, file.filename, role, experience)
        
        if "error" in report:
             return jsonify({"success": False, "error": report["error"]}), 400

        return jsonify({"success": True, "report": report}), 200

    except Exception as e:
        print(f"Erro na análise de CV: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
