from flask import Blueprint, request, jsonify
import os
import json
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

from utils.secrets import get_secret

services_bp = Blueprint("services", __name__)

# Lazy initialization for Brevo API
_api_instance = None

def get_brevo_api():
    """Initialize the Brevo API client. Creates fresh instance each time."""
    configuration = sib_api_v3_sdk.Configuration()
    api_key = get_secret("BREVO_API_KEY")
    configuration.api_key["api-key"] = api_key
    return sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

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
        
        # Dados de Serviço e Pagamento Dinâmicos
        service_name = data.get("service", "Revisão de CV") # Ex: "Revisão de CV", "Pack Completo"
        amount = data.get("amount", "20.00") # Default atualizado para 20.00
        
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
        
        print(f"Dados extraídos: nome={name}, email={email}, telefone={phone}, serviço={service_name}, valor={amount}")

        # Validar dados essenciais
        if not all([name, email, phone]):
             return jsonify({"success": False, "error": "Dados obrigatórios em falta (Nome, Email, Telefone)"}), 400

        # >>> 1. Iniciar Pagamento MB WAY <<<
        payment_data = {
            "amount": amount,
            "orderId": data.get("orderId", f"CV-{name.replace(' ', '')}-{int(pd.Timestamp.now().timestamp())}" if 'pd' in locals() else f"CV-{name.replace(' ', '')}"),
            "phone": phone,
            "email": email,
            "description": f"{service_name} - {name}"
        }
        
        # Normalizar e criar pagamento
        print(f"Iniciando pagamento MB WAY de {amount}€ para {name}...")
        normalized_payment = normalize_payment_data(payment_data)
        payment_result = create_mbway_payment(normalized_payment)
        
        if not payment_result.get('success'):
            print(f"Erro ao criar pagamento: {payment_result.get('error')}")
            # Retornamos erro se pagamento falhar
            return jsonify({"success": False, "error": f"Erro ao iniciar pagamento MB WAY: {payment_result.get('error')}"}), 400

        # >>> 2. Enviar Email 2 (Pedido e Link de Pagamento)
        from utils.email import send_email_with_attachments, get_email_template_2
        
        # O link de pagamento real viria do payment_result se existir na API
        payment_link = payment_result.get('payment_url', "https://share2inspire.pt/pagamento")
        html_content = get_email_template_2(name, payment_link)
        
        success, msg = send_email_with_attachments(
            email, name, "Confirmação do pedido | Pagamento Revisão Profissional de CV", html_content
        )

        try:
            get_brevo_api().send_transac_email(sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": email, "name": name}],
                subject="Confirmação do pedido | Pagamento Revisão Profissional de CV",
                html_content=html_content
            ))
        except ApiException as e:
            print(f"Erro Brevo: {e}")
            # Se o email falhar, mas o pagamento foi iniciado, avisamos o user
            return jsonify({
                "success": True, 
                "message": "Pagamento iniciado, mas erro ao enviar email de confirmação. Contacte o suporte.",
                "payment": payment_result,
                "warning": str(e)
            }), 200

        return jsonify({
            "success": True, 
            "message": "O teu pedido foi recebido. Assim que o pagamento for confirmado, receberás um email com os próximos passos.",
            "payment": payment_result
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
        
        # Log da forma de pagamento, se recebida
        payment_method = data.get('payment_method')
        logger.info(f"Pagamento via: {payment_method if payment_method else 'Não especificado'}")

        if not email or not name:
            return jsonify({"success": False, "error": "Email e Nome obrigatórios"}), 400
            
        # Verificar se é para usar template (frontend envia templateId)
        template_id = data.get('templateId')
        params = data.get('params')

        recipients = [{"email": email, "name": name}]
        admin_email = {"email": "srshare2inspire@gmail.com", "name": "Admin Share2Inspire"}
        
        # Enviar também para admin (como BCC ou TO adicional)
        # Brevo API permite array em 'to' ou 'bcc'
        
        if template_id:
            # Usar Template do Brevo
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=recipients,
                bcc=[admin_email],
                template_id=int(template_id),
                params=params
            )
        else:
            # Fallback Manual
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
                to=recipients,
                bcc=[admin_email],
                sender={"email": os.getenv("BREVO_SENDER_EMAIL", "noreply@share2inspire.pt"), "name": "Share2Inspire"},
                subject=subject,
                html_content=html_content
            )
        
        try:
            get_brevo_api().send_transac_email(send_smtp_email)
            return jsonify({"success": True, "message": "Email enviado com sucesso"})
        except ApiException as e:
            print(f"Erro Brevo: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
            
    except Exception as e:
        print(f"Erro no endpoint kickstart-email: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@services_bp.route("/analyze-cv", methods=["POST"])
def analyze_cv():
    """
    CV Analyzer - Paid Service Flow
    1. Analyze CV
    2. Create MBWAY payment
    3. Send Email 3 with payment link
    4. Return confirmation message (NOT the report - delivered via email after payment)
    """
    try:
        from utils.analysis import CVAnalyzer
        from routes.payment import create_mbway_payment, normalize_payment_data
        from utils.email import send_email_with_attachments, get_email_template_3
        
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
        email = data.get('email', '')
        name = data.get('name', '')
        phone = data.get('phone', '')
        
        if not all([email, name, phone]):
            return jsonify({"success": False, "error": "Dados obrigatórios em falta (Email, Nome, Telefone)"}), 400
        
        # Executar análise
        analyzer = CVAnalyzer()
        report = analyzer.analyze(file, file.filename, role, experience)
        
        if "error" in report:
             return jsonify({"success": False, "error": report["error"]}), 400

        # Guardar análise temporariamente para envio posterior (após pagamento)
        # TODO: Implementar storage temporário (Redis, DB, ou filesystem)
        # Por agora o relatório será regenerado no callback de pagamento
        
        # >>> 1. Iniciar Pagamento MB WAY <<<
        import pandas as pd
        payment_data = {
            "amount": "1.00",  # CV Analyzer = 1€
            "orderId": f"CVA-{name.replace(' ', '')}-{int(pd.Timestamp.now().timestamp())}",
            "phone": phone,
            "email": email,
            "description": f"CV Analyzer - {name}"
        }
        
        # Normalizar e criar pagamento
        print(f"Iniciando pagamento MB WAY de 1€ para {name}...")
        normalized_payment = normalize_payment_data(payment_data)
        payment_result = create_mbway_payment(normalized_payment)
        
        if not payment_result.get('success'):
            print(f"Erro ao criar pagamento: {payment_result.get('error')}")
            return jsonify({"success": False, "error": f"Erro ao iniciar pagamento MB WAY: {payment_result.get('error')}"}), 400

        # >>> 2. Enviar Email 3 (Análise Concluída + Link de Pagamento) <<<
        payment_link = payment_result.get('payment_url', "https://share2inspire.pt/pagamento")
        html_content = get_email_template_3(name, payment_link)
        
        success, msg = send_email_with_attachments(
            email, name, "Relatório de Análise de CV | Pagamento para acesso completo", html_content
        )
        
        if not success:
            print(f"Erro ao enviar email: {msg}")
            # Se email falhar mas pagamento foi criado, avisamos
            return jsonify({
                "success": True, 
                "message": "Pagamento iniciado, mas erro ao enviar email. Contacte o suporte.",
                "payment": payment_result,
                "warning": msg
            }), 200
        
        # >>> 3. Retornar Mensagem de Confirmação (FALLBACK MESSAGE) <<<
        return jsonify({
            "success": True, 
            "message": "O teu pedido foi recebido. Assim que o pagamento for confirmado, receberás um email com os próximos passos.",            "payment": payment_result
        }), 200

    except Exception as e:
        print(f"Erro na análise de CV: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@services_bp.route("/deliver-report", methods=["POST"])
def deliver_report():
    """
    Final delivery of the paid report via email with 2 attachments.
    Implements the 'Guia de Escrita Editorial' requirements and Success Checklist.
    """
    try:
        import base64
        from utils.report_pdf import ReportPDFGenerator
        
        # 1. Capture Data
        report_json = request.form.get("report")
        if not report_json:
            return jsonify({"success": False, "error": "Dados do relatório ausentes"}), 400
        report_data = json.loads(report_json)
        
        cv_file = request.files.get("cv_file")
        email = request.form.get("email")
        name = request.form.get("name")
        
        if not all([cv_file, email, name]):
            return jsonify({"success": False, "error": "Ficheiro original ou dados de contacto ausentes"}), 400

        # 2. SUCCESS CHECKLIST & PDF GENERATION
        generator = ReportPDFGenerator()
        pdf_bytes, status = generator.create_pdf(report_data)
        
        # System Rule: PDF must exist, >50KB, >=5 pages
        if status != "OK":
            print(f"Validation Checklist Failed: {status}")
            # Fallback message as requested
            return jsonify({
                "success": True, 
                "prepared": True, 
                "message": "A análise está a ser preparada com detalhe editorial. Receberá o relatório no seu email em instantes."
            }), 200
            
        cv_content = cv_file.read()
        if not cv_content:
             return jsonify({"success": False, "error": "CV original está vazio"}), 400

        # 3. Preparation of Attachments
        safe_name = name.replace(" ", "_")
        orig_filename = cv_file.filename or "Curriculo.pdf"
        ext = os.path.splitext(orig_filename)[1] or ".pdf"
        
        attachments = [
            {
                "content": base64.b64encode(pdf_bytes).decode('utf-8'),
                "name": f"Relatorio_Analise_CV_{safe_name}.pdf"
            },
            {
                "content": base64.b64encode(cv_content).decode('utf-8'),
                "name": f"CV_{safe_name}_Original{ext}"
            }
        ]

        # 4. Premium Branded Email Content (Template 4)
        from utils.email import send_email_with_attachments, get_email_template_4
        email_html = get_email_template_4(name)

        # 5. Send Transactional Email
        success, msg = send_email_with_attachments(
            to_email=email,
            to_name=name,
            subject=f"Relatório de Análise de CV | {name}",
            html_content=email_html,
            attachments=attachments
        )

        if success:
            return jsonify({"success": True, "message": "Relatório enviado com sucesso!"}), 200
        else:
            return jsonify({"success": False, "error": f"Erro ao enviar email: {msg}"}), 500

    except Exception as e:
        print(f"Erro na entrega do relatório: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
        return jsonify({"success": False, "error": str(e)}), 500
