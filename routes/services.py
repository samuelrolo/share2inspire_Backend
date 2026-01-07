from flask import Blueprint, request, jsonify
import os
import json
import logging
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from dotenv import load_dotenv
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

from utils.secrets import get_secret

# Logger configuration
logger = logging.getLogger(__name__)

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

        # >>> 1. Enviar EMAIL 1: Confirmação de Pedido <<<
        from email_templates.transactional_emails import get_email_confirmacao_pedido
        from datetime import datetime
        
        data_pedido = datetime.now().strftime('%d/%m/%Y')
        subject_1, body_1 = get_email_confirmacao_pedido(
            nome=name,
            nome_do_servico=service_name,
            data_pedido=data_pedido
        )
        
        try:
            get_brevo_api().send_transac_email(sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": email, "name": name}],
                subject=subject_1,
                html_content=body_1.replace('\n', '<br>')
            ))
        except ApiException as e:
            print(f"Erro ao enviar EMAIL 1: {e}")
        
        # >>> 2. Iniciar Pagamento MB WAY <<<
        from routes.payment import create_mbway_payment, normalize_payment_data
        
        timestamp = int(datetime.now().timestamp())
        payment_data = {
            "amount": amount,
            "orderId": data.get("orderId", f"CV-{name.replace(' ', '')}-{timestamp}"),
            "phone": phone,
            "email": email,
            "description": f"{service_name} - {name}"
        }
        
        print(f"Iniciando pagamento MB WAY de {amount}€ para {name}...")
        normalized_payment = normalize_payment_data(payment_data)
        payment_result = create_mbway_payment(normalized_payment)
        
        if not payment_result.get('success'):
            print(f"Erro ao criar pagamento: {payment_result.get('error')}")
            return jsonify({
                "success": False, 
                "error": f"Erro ao iniciar pagamento MB WAY: {payment_result.get('error')}"
            }), 400

        # >>> 3. Enviar EMAIL 2: Pagamento MB Way <<<
        from email_templates.transactional_emails import get_email_pagamento_mbway
        
        # Determinar prazo de entrega baseado no serviço
        prazo_map = {
            "CV Analyzer": "Imediato (após confirmação)",
            "Revisão de CV": "3 dias úteis",
            "Kickstart Pro": "Conforme horário agendado"
        }
        prazo_entrega = prazo_map.get(service_name, "A definir")
        
        payment_link = payment_result.get('payment_url', f"https://share2inspire.pt/pages/pagamento.html?orderId={payment_data['orderId']}")
        
        subject_2, body_2 = get_email_pagamento_mbway(
            nome=name,
            nome_do_servico=service_name,
            valor=f"{amount}€",
            prazo_entrega=prazo_entrega,
            link_pagamento_mbway=payment_link
        )
        
        try:
            get_brevo_api().send_transac_email(sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": email, "name": name}],
                subject=subject_2,
                html_content=body_2.replace('\n', '<br>')
            ))
        except ApiException as e:
            print(f"Erro ao enviar EMAIL 2: {e}")
            return jsonify({
                "success": True, 
                "message": "Pagamento iniciado, mas erro ao enviar email de confirmação. Contacte o suporte.",
                "payment": payment_result,
                "warning": str(e)
            }), 200

        return jsonify({
            "success": True, 
            "message": "Pedido confirmado! Verifica o teu email para concluir o pagamento.",
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

@services_bp.route("/analyze-cv", methods=["POST", "OPTIONS"])
def analyze_cv():
    """
    CV Analyzer - FREE Analysis Flow
    Returns analysis results directly to show on screen.
    Payment is handled separately when user chooses to get full report.
    """
    # Tratar pedidos OPTIONS para CORS
    if request.method == "OPTIONS":
        from flask import make_response
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response, 200
    
    try:
        from utils.analysis import CVAnalyzer
        
        logger.info("="*50)
        logger.info("Endpoint /api/services/analyze-cv chamado (FREE ANALYSIS)")
        
        # Validar ficheiro
        if 'cv_file' not in request.files:
            logger.error("Ficheiro cv_file não encontrado no request")
            logger.info(f"Files recebidos: {list(request.files.keys())}")
            return jsonify({"success": False, "error": "Ficheiro não encontrado"}), 400
            
        file = request.files['cv_file']
        if file.filename == '':
            logger.error("Nome de ficheiro vazio")
            return jsonify({"success": False, "error": "Nome de ficheiro inválido"}), 400

        logger.info(f"Ficheiro recebido: {file.filename}")
        
        # Validar outros dados (apenas nome para personalização)
        data = request.form
        role = data.get('current_role', '')
        experience = data.get('experience', '')
        name = data.get('name', 'Candidato')
        
        logger.info(f"Dados: role={role}, experience={experience}, name={name}")
        
        # Executar análise
        logger.info("Inicializando CVAnalyzer...")
        analyzer = CVAnalyzer()
        logger.info(f"CVAnalyzer inicializado. API Key presente: {analyzer.api_key is not None}")
        logger.info(f"Model inicializado: {analyzer.model is not None}")
        
        logger.info("Iniciando análise do CV...")
        report = analyzer.analyze(file, file.filename, role, experience)
        logger.info(f"Análise concluída. Tem erro: {'error' in report}")
        
        if "error" in report:
            logger.error(f"Erro na análise: {report['error']}")
            return jsonify({"success": False, "error": report["error"]}), 400

        logger.info("Retornando resultado com sucesso")
        logger.info("="*50)
        
        # Retornar análise diretamente (SEM pagamento)
        return jsonify({
            "success": True,
            "report": report,
            "message": "Análise concluída com sucesso!"
        }), 200

    except Exception as e:
        logger.exception(f"Erro crítico na análise de CV: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@services_bp.route("/request-report-payment", methods=["POST", "OPTIONS"])
def request_report_payment():
    """
    CV Analyzer - Request paid report (1€ MB WAY)
    Called when user clicks "Quero Relatório Personalizado"
    """
    # Tratar pedidos OPTIONS para CORS
    if request.method == "OPTIONS":
        from flask import make_response
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response, 200
    
    try:
        from routes.payment import create_mbway_payment, normalize_payment_data
        from datetime import datetime
        from email_templates.transactional_emails import (
            get_email_confirmacao_pedido,
            get_email_pagamento_mbway
        )
        
        print("Endpoint /api/services/request-report-payment chamado")
        
        data = request.get_json()
        email = data.get('email', '')
        name = data.get('name', 'Candidato')
        phone = data.get('phone', '')
        
        if not all([email, phone]):
            return jsonify({"success": False, "error": "Email e Telemóvel são obrigatórios"}), 400
        
        # >>> 1. Enviar EMAIL 1: Confirmação de Pedido <<<
        data_pedido = datetime.now().strftime('%d/%m/%Y')
        subject_1, body_1 = get_email_confirmacao_pedido(
            nome=name,
            nome_do_servico="CV Analyzer",
            data_pedido=data_pedido
        )
        
        try:
            get_brevo_api().send_transac_email(sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": email, "name": name}],
                subject=subject_1,
                html_content=body_1.replace('\n', '<br>')
            ))
        except ApiException as e:
            print(f"Aviso: Erro ao enviar EMAIL 1: {e}")
        
        # >>> 2. Criar pagamento MB WAY <<<
        timestamp = int(datetime.now().timestamp())
        payment_data = {
            "amount": "1.00",
            "orderId": f"CVA-{name.replace(' ', '')}-{timestamp}",
            "phone": phone,
            "email": email,
            "description": f"CV Analyzer Report - {name}"
        }
        
        normalized_payment = normalize_payment_data(payment_data)
        payment_result = create_mbway_payment(normalized_payment)
        
        if not payment_result.get('success'):
           return jsonify({"success": False, "error": f"Erro MB WAY: {payment_result.get('error')}"}), 400

        # >>> 3. Enviar EMAIL 2: Pagamento MB Way <<<
        payment_link = payment_result.get('payment_url', f"https://share2inspire.pt/pages/pagamento.html?orderId={payment_data['orderId']}")
        
        subject_2, body_2 = get_email_pagamento_mbway(
            nome=name,
            nome_do_servico="CV Analyzer",
            valor="1€",
            prazo_entrega="Imediato (após confirmação)",
            link_pagamento_mbway=payment_link
        )
        
        try:
            get_brevo_api().send_transac_email(sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": email, "name": name}],
                subject=subject_2,
                html_content=body_2.replace('\n', '<br>')
            ))
        except ApiException as e:
            print(f"Aviso: Erro ao enviar EMAIL 2: {e}")

        return jsonify({
            "success": True,
            "message": "Pedido confirmado! Verifica o teu email e telemóvel para concluir o pagamento.",
            "payment": payment_result,
            "requestId": payment_result.get('requestId')
        }), 200

    except Exception as e:
        print(f"Erro no pagamento do relatório: {e}")
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

        # 4. Premium Branded Email Content (EMAIL 3: Entrega do Relatório)
        from email_templates.transactional_emails import get_email_entrega_relatorio
        
        subject_3, body_3 = get_email_entrega_relatorio(
            nome=name,
            nome_do_servico="CV Analyzer"
        )

        # 5. Send Transactional Email with Attachments
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": email, "name": name}],
            bcc=[{"email": "srshare2inspire@gmail.com", "name": "Admin Share2Inspire"}],
            sender={"email": os.getenv("BREVO_SENDER_EMAIL", "srshare2inspire@gmail.com"), "name": "Share2Inspire"},
            subject=subject_3,
            html_content=body_3.replace('\n', '<br>'),
            attachment=attachments
        )
        
        try:
            get_brevo_api().send_transac_email(send_smtp_email)
            return jsonify({"success": True, "message": "Relatório enviado com sucesso!"}), 200
        except ApiException as e:
            print(f"Erro ao enviar email: {e}")
            return jsonify({"success": False, "error": f"Erro ao enviar email: {str(e)}"}), 500

    except Exception as e:
        print(f"Erro na entrega do relatório: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@services_bp.route("/kickstart-confirm", methods=["POST"])
def kickstart_confirm():
    """
    Kickstart Pro Confirmation + Payment Request
    Handles the new flow: 1. Schedule (FE) -> 2. Confirm (here) -> 3. Payment & Email
    """
    try:
        from routes.payment import create_mbway_payment, normalize_payment_data
        from utils.email import send_email_with_attachments, get_email_template_kickstart_v2
        from datetime import datetime
        import urllib.parse
        
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        # objectives = data.get('objectives') # Logging optional
        
        if not all([name, email, phone]):
            return jsonify({"success": False, "error": "Nome, Email e Telemóvel são obrigatórios"}), 400
            
        print(f"Kickstart Request: {name} ({email}) - {phone}")

        # 1. Initiate MB WAY Payment (Push Notification)
        timestamp = int(datetime.now().timestamp())
        payment_data = {
            "amount": "35.00",
            "orderId": f"KSP-{timestamp}",
            "phone": phone,
            "email": email,
            "description": f"Kickstart Pro - {name}"
        }
        
        normalized = normalize_payment_data(payment_data)
        payment_result = create_mbway_payment(normalized)
        
        if not payment_result.get('success'):
            print(f"Aviso MB WAY Kickstart: {payment_result.get('error')}")
            # Continue anyway to send email with link
        
        # 2. Prepare Confirmation Email with Fallback Link
        params = {
            "service": "kickstart-pro",
            "amount": "35",
            "phone": phone,
            "email": email,
            "name": name
        }
        encoded_params = urllib.parse.urlencode(params)
        fallback_link = f"https://share2inspire.pt/pages/pagamento.html?{encoded_params}"
        
        email_html = get_email_template_kickstart_v2(name, fallback_link)
        
        # 3. Send Email
        email_success, email_msg = send_email_with_attachments(
            to_email=email,
            to_name=name,
            subject="Confirmação de Agendamento - Kickstart Pro",
            html_content=email_html
        )
        
        message = "Pedido recebido com sucesso. "
        if payment_result.get('success'):
            message += "Verifique o seu telemóvel (MB WAY) para confirmar o pagamento."
        else:
             message += "Verifique o seu email para concluir o pagamento."

        return jsonify({
            "success": True, 
            "payment_started": payment_result.get('success', False),
            "email_sent": email_success,
            "message": message
        }), 200

    except Exception as e:
        print(f"Erro Kickstart Confirm: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
