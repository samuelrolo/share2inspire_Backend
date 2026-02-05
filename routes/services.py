from flask import Blueprint, request, jsonify
import os
import json
import matplotlib.pyplot as plt
import numpy as np
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

# Whitelist de emails para bypass de pagamento (testes/admin)
WHITELIST_EMAILS = [
    "samuelrolo@gmail.com",
    "srshare2inspire@gmail.com"
]

# Sender padrão para emails Brevo
BREVO_SENDER = {"email": "srshare2inspire@gmail.com", "name": "Share2Inspire"}

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
        amount = data.get("amount", "2.99") # Default atualizado para 20.00
        
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
        
        # Registar análise no Supabase para tracking
        try:
            from utils.analytics import CVAnalytics
            analytics = CVAnalytics()
            analytics.log_analysis(
                user_name=name,
                user_email=data.get('email', ''),
                analysis_result=report,
                payment_status='pending'
            )
            logger.info("Análise registada no Supabase com sucesso")
        except Exception as e:
            logger.warning(f"Erro ao registar análise no Supabase: {e}")
        
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
    CV Analyzer - Request paid report (2.99€ MB WAY)
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
        from utils.datastore_client import get_datastore_client
        import base64
        
        print("Endpoint /api/services/request-report-payment chamado")
        
        # >>> ACCEPT FORMDATA with CV file <<<
        email = request.form.get('email', '')
        name = request.form.get('name', 'Candidato')
        phone = request.form.get('phone', '')
        analysis_data_str = request.form.get('analysis_data', '{}')
        analysis_data = json.loads(analysis_data_str) if analysis_data_str else {}
        
        # Extract CV file
        cv_file = request.files.get('cv_file')
        cv_data = None
        
        if cv_file:
            print(f"[CV FILE] Recebido: {cv_file.filename}, tipo: {cv_file.content_type}")
            # Convert to base64 for storage
            cv_bytes = cv_file.read()
            cv_base64 = base64.b64encode(cv_bytes).decode('utf-8')
            cv_data = {
                'base64': cv_base64,
                'filename': cv_file.filename,
                'content_type': cv_file.content_type
            }
            print(f"[CV FILE] Convertido para base64 ({len(cv_base64)} chars)")
        else:
            print("[CV FILE] AVISO: Nenhum CV file recebido!")
        
        if not all([email, phone]):
            return jsonify({"success": False, "error": "Email e Telemóvel são obrigatórios"}), 400
        
        # >>> WHITELIST CHECK: Bypass de pagamento para emails de teste/admin <<<
        if email.lower() in [e.lower() for e in WHITELIST_EMAILS]:
            print(f"[WHITELIST] Email {email} está na whitelist - bypass de pagamento")
            return jsonify({
                "success": True,
                "message": "Email na whitelist - relatório será enviado automaticamente!",
                "payment": {"success": True, "status": "whitelist_bypass"},
                "requestId": f"WL-{name.replace(' ', '')}-{int(datetime.now().timestamp())}",
                "orderId": f"WL-{name.replace(' ', '')}-{int(datetime.now().timestamp())}",
                "whitelist": True,
                "skipPayment": True
            }), 200
        
        # >>> EMAILS OBSOLETOS REMOVIDOS <<<
        # O pagamento é feito no ecrã, não enviamos emails de pedido
        # O email correto (com CV e relatório) é enviado após confirmação via deliver_report_internal()
        
        # >>> 2. Criar pagamento MB WAY <<<
        timestamp = int(datetime.now().timestamp())
        payment_data = {
            "amount": "2.99",
            "orderId": f"CVA-{name.replace(' ', '')}-{timestamp}",
            "phone": phone,
            "email": email,
            "description": f"CV Analyzer Report - {name}"
        }
        
        normalized_payment = normalize_payment_data(payment_data)
        payment_result = create_mbway_payment(normalized_payment)
        
        if not payment_result.get('success'):
           return jsonify({"success": False, "error": f"Erro MB WAY: {payment_result.get('error')}"}), 400

        # >>> 2.5 SALVAR NO DATASTORE COM CV FILE (CRÍTICO) <<<
        get_datastore_client().save_payment_record(
            order_id=payment_data['orderId'],
            payment_data=payment_result,
            user_data={
                "name": name,
                "email": email,
                "phone": phone,
                "description": payment_data['description']
            },
            analysis_data=analysis_data,
            cv_data=cv_data  # ✅ CV em base64 guardado!
        )
        print(f"[REQUEST-PAYMENT] Registo guardado para {payment_data['orderId']} {'COM CV' if cv_data else 'SEM CV'}")

        # >>> EMAIL 2 REMOVIDO (OBSOLETO) <<<
        # O email de entrega (com anexos) é enviado após confirmação de pagamento
        # via deliver_report_internal() no webhook

        return jsonify({
            "success": True,
            "message": "Pedido confirmado! Verifica o teu email e telemóvel para concluir o pagamento.",
            "payment": payment_result,
            "requestId": payment_data['orderId'],  # Usar o orderId que enviámos à Ifthenpay para polling
            "orderId": payment_data['orderId'],
            "ifthenpayRequestId": payment_result.get('requestId')  # RequestId da Ifthenpay (para referência)
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
        email = request.form.get("email")
        name = request.form.get("name")
        
        if not report_json:
            return jsonify({"success": False, "error": "Dados do relatório ausentes"}), 400
        report_data = json.loads(report_json)
        
        # --- NORMALIZAÇÃO DE DADOS (BLINDAGEM) ---
        def ensure_keys(d, keys_defaults):
            for key, default in keys_defaults.items():
                if key not in d or d[key] is None:
                    d[key] = default
                elif isinstance(default, dict) and isinstance(d[key], dict):
                    ensure_keys(d[key], default)
        
        required_structure = {
            "candidate_profile": {
                "detected_name": name or "Candidato",
                "detected_role": "Não identificado",
                "detected_sector": "Não identificado",
                "total_years_exp": "N/D",
                "seniority": "N/D",
                "education_level": "N/D",
                "languages_detected": [],
                "key_skills": []
            },
            "global_summary": {
                "strengths": ["Análise baseada em estrutura concluída"],
                "improvements": ["Otimização de conteúdo recomendada"]
            },
            "executive_summary": {
                "global_score": 70,
                "global_score_breakdown": {
                    "structure_clarity": 70,
                    "content_relevance": 70,
                    "risks_inconsistencies": 70,
                    "ats_compatibility": 70,
                    "impact_results": 70,
                    "personal_brand": 70
                },
                "market_positioning": "Análise de posicionamento disponível no relatório.",
                "key_decision_factors": "Fatores de decisão detalhados no PDF."
            },
            "diagnostic_impact": {
                "first_30_seconds_read": "Análise de impacto inicial.",
                "impact_strengths": "Pontos fortes identificados.",
                "impact_strengths_signal": "Sinal positivo.",
                "impact_strengths_missing": "Melhorias pendentes.",
                "impact_dilutions": "Áreas de diluição."
            },
            "content_structure_analysis": {
                "organization_hierarchy": "Hierarquia da informação.",
                "organization_hierarchy_signal": "Sinal de organização.",
                "organization_hierarchy_missing": "Melhorias estruturais.",
                "responsibilities_results_balance": "Equilíbrio de conteúdo.",
                "responsibilities_results_balance_signal": "Sinal de equilíbrio.",
                "orientation": "Orientação para resultados."
            },
            "ats_digital_recruitment": {
                "compatibility": "Compatibilidade básica com ATS.",
                "filtering_risks": "Riscos de filtragem analisados.",
                "alignment": "Alinhamento com práticas de mercado."
            },
            "skills_differentiation": {
                "technical_behavioral_analysis": "Análise de competências.",
                "differentiation_factors": "Fatores de diferenciação.",
                "common_undifferentiated": "Elementos comuns identificados."
            },
            "strategic_risks": {
                "identified_risks": "Riscos estratégicos analisados."
            },
            "languages_analysis": {
                "languages_assessment": "Avaliação de idiomas."
            },
            "education_analysis": {
                "education_assessment": "Avaliação de formação académica."
            },
            "priority_recommendations": {
                "immediate_adjustments": "Ajustes imediatos recomendados.",
                "refinement_areas": "Áreas de refinamento identificadas.",
                "deep_repositioning": "Sugestões de reposicionamento."
            },
            "market_analysis": {
                "sector_trends": "Tendências do setor.",
                "competitive_landscape": "Panorama competitivo.",
                "opportunities_threats": "Oportunidades e ameaças."
            },
            "executive_conclusion": {
                "potential_after_improvements": "Potencial de evolução identificado.",
                "expected_competitiveness": "Competitividade esperada no mercado."
            },
            "final_conclusion": {
                "executive_synthesis": "Síntese executiva final.",
                "next_steps": "Próximos passos recomendados."
            },
            "pdf_extended_content": {
                "sector_analysis": {
                    "identified_sector": "Setor não identificado",
                    "sector_trends": "Tendências não disponíveis.",
                    "competitive_landscape": "Panorama não disponível."
                },
                "critical_certifications": []
            },
            "phrase_improvements": [],
            "sentence_improvements": []
        }
        ensure_keys(report_data, required_structure)
        
        # VALIDAÇÃO ADICIONAL: Limpar detected_name se contiver texto bruto
        if 'candidate_profile' in report_data and 'detected_name' in report_data['candidate_profile']:
            detected_name = report_data['candidate_profile']['detected_name']
            # Se o nome tiver mais de 100 caracteres, é texto bruto do CV, não um nome
            if len(detected_name) > 100:
                print(f"[AVISO] detected_name contém texto bruto ({len(detected_name)} caracteres). Substituindo pelo nome do formulário.")
                report_data['candidate_profile']['detected_name'] = name or "Candidato"
        # -----------------------------------------
        
        cv_file = request.files.get("cv_file")
        
        if not all([cv_file, email, name]):
            return jsonify({"success": False, "error": "Ficheiro original ou dados de contacto ausentes"}), 400

        # 2. SUCCESS CHECKLIST & PDF GENERATION
        generator = ReportPDFGenerator()
        # Generate radar chart
        radar_scores = {
            "Estrutura": report_data.get("executive_summary", {}).get("global_score_breakdown", {}).get("structure_clarity", 0),
            "Conteúdo": report_data.get("executive_summary", {}).get("global_score_breakdown", {}).get("content_relevance", 0),
            "Consistência": report_data.get("executive_summary", {}).get("global_score_breakdown", {}).get("risks_inconsistencies", 0),
            "ATS": report_data.get("executive_summary", {}).get("global_score_breakdown", {}).get("ats_compatibility", 0),
            "Impacto": report_data.get("executive_summary", {}).get("global_score_breakdown", {}).get("impact_results", 0),
            "Marca Pessoal": report_data.get("executive_summary", {}).get("global_score_breakdown", {}).get("personal_brand", 0)
        }
        
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_radar:
            radar_chart_path = tmp_radar.name
            create_radar_chart(radar_scores, radar_chart_path)

        pdf_buffer, pdf_filename = generator.create_pdf(report_data, radar_chart_path=radar_chart_path)
        pdf_bytes = pdf_buffer.getvalue()
        
        # Clean up temporary radar chart file
        if os.path.exists(radar_chart_path):
            os.unlink(radar_chart_path)
        
        # System Rule: PDF must exist
        if not pdf_bytes or len(pdf_bytes) < 1024:
            print(f"Validation Checklist Failed: PDF too small or empty")
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
            print(f"[DEBUG] Tentando enviar email para {email} via Brevo...")
            print(f"[DEBUG] Tamanho do PDF: {len(pdf_bytes)} bytes")
            print(f"[DEBUG] Tamanho do CV: {len(cv_content)} bytes")
            print(f"[DEBUG] Total de anexos: {len(attachments)}")
            api_instance = get_brevo_api()
            print(f"[DEBUG] API instance criada com sucesso")
            api_response = api_instance.send_transac_email(send_smtp_email)
            print(f"[DEBUG] Resposta da Brevo: {api_response}")
            print(f"[DEBUG] Email enviado com sucesso!")
            return jsonify({"success": True, "message": "Relatório enviado com sucesso!"}), 200
        except ApiException as e:
            print(f"[ERRO] Falha na API da Brevo: {e}")
            return jsonify({"success": False, "error": f"Erro na API da Brevo: {str(e)}"}), 500
        except Exception as e:
            print(f"[ERRO] Erro inesperado no envio: {e}")
            return jsonify({"success": False, "error": f"Erro inesperado: {str(e)}"}), 500

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

def deliver_report_internal(order_id, analysis_data, user_data):
    """
    Internal function to deliver report after confirmed payment.
    Handles distinct inputs from the public endpoint.
    """
    try:
        import base64
        import tempfile
        import os
        from utils.report_pdf import ReportPDFGenerator
        from utils.analytics import analytics
        from email_templates.transactional_emails import get_email_entrega_relatorio
        
        print(f"[INTERNAL DELIVERY] Processing order {order_id}")
        name = user_data.get('name', 'Cliente')
        email = user_data.get('email')

        if not email:
            return {"success": False, "error": "Email required"}

        # 1. Generate PDF
        generator = ReportPDFGenerator()
        
        # Generate radar chart (reusing logic from public endpoint)
        radar_scores = {
            "Estrutura": analysis_data.get("executive_summary", {}).get("global_score_breakdown", {}).get("structure_clarity", 0),
            "Conteúdo": analysis_data.get("executive_summary", {}).get("global_score_breakdown", {}).get("content_relevance", 0),
            "Consistência": analysis_data.get("executive_summary", {}).get("global_score_breakdown", {}).get("risks_inconsistencies", 0),
            "ATS": analysis_data.get("executive_summary", {}).get("global_score_breakdown", {}).get("ats_compatibility", 0),
            "Impacto": analysis_data.get("executive_summary", {}).get("global_score_breakdown", {}).get("impact_results", 0),
            "Marca Pessoal": analysis_data.get("executive_summary", {}).get("global_score_breakdown", {}).get("personal_brand", 0)
        }
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_radar:
            radar_chart_path = tmp_radar.name
            create_radar_chart(radar_scores, radar_chart_path)

        pdf_buffer, pdf_filename = generator.create_pdf(analysis_data, radar_chart_path=radar_chart_path)
        pdf_bytes = pdf_buffer.getvalue()
        
        # Cleanup
        if os.path.exists(radar_chart_path):
            os.unlink(radar_chart_path)
        
        # 2. Attachments - Include CV if stored in Datastore
        from utils.datastore_client import get_datastore_client
        safe_name = name.replace(" ", "_")
        attachments = [
            {
                "content": base64.b64encode(pdf_bytes).decode('utf-8'),
                "name": f"Relatorio_Analise_CV_{safe_name}.pdf"
            }
        ]
        
        # >>> RETRIEVE CV FROM DATASTORE <<<
        record = get_datastore_client().get_payment_record(order_id)
        if record and record.get('cv_data'):
            cv_data = record['cv_data']
            cv_base64 = cv_data.get('base64')
            cv_filename = cv_data.get('filename', 'CV_Original.pdf')
            
            if cv_base64:
                # CV already in base64, just add to attachments
                attachments.append({
                    "content": cv_base64,
                    "name": cv_filename
                })
                print(f"[INTERNAL DELIVERY] ✅ CV anexado: {cv_filename}")
            else:
                print("[INTERNAL DELIVERY] ⚠️ CV data sem base64")
        else:
            print("[INTERNAL DELIVERY] ⚠️ Nenhum CV encontrado no Datastore")

        # 3. Send Email
        subject_3, body_3 = get_email_entrega_relatorio(
            nome=name,
            nome_do_servico="CV Analyzer"
        )
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": email, "name": name}],
            bcc=[{"email": "srshare2inspire@gmail.com", "name": "Admin Share2Inspire"}],
            sender={"email": os.getenv("BREVO_SENDER_EMAIL", "srshare2inspire@gmail.com"), "name": "Share2Inspire"},
            subject=subject_3,
            html_content=body_3.replace('\n', '<br>'),
            attachment=attachments
        )
        
        api_instance = get_brevo_api()
        api_instance.send_transac_email(send_smtp_email)
        print(f"[INTERNAL DELIVERY] Email sent to {email}")

        # 4. UPDATE ANALYTICS STATUS
        print(f"[INTERNAL DELIVERY] Updating analytics for {email}")
        analytics.update_payment_status_by_email(email, "paid", user_data.get('amount'))

        return {"success": True}

    except Exception as e:
        print(f"[INTERNAL DELIVERY] Error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def create_radar_chart(scores, output_path):
    labels = list(scores.keys())
    stats = list(scores.values())
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    stats = np.concatenate((stats,[stats[0]]))
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles, stats, color="#BF9A33", alpha=0.25)
    ax.plot(angles, stats, color="#BF9A33", linewidth=2)
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    plt.savefig(output_path)
    plt.close(fig)


@services_bp.route("/pedido-consulta", methods=["POST", "OPTIONS"])
def pedido_consulta():
    """
    Endpoint para receber pedidos de consulta do serviço de Criação de Conteúdos Online.
    Envia email de confirmação ao cliente e notificação para o admin.
    """
    # Handle CORS preflight
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response, 200
    
    try:
        # Obter dados do formulário
        nome = request.form.get('nome')
        email = request.form.get('email')
        assunto = request.form.get('assunto')
        mensagem = request.form.get('mensagem')
        anexo = request.files.get('anexo')
        
        logger.info(f"Pedido de consulta recebido: {nome} ({email}) - {assunto}")
        
        # Validação de campos obrigatórios
        if not nome or not email or not assunto or not mensagem:
            return jsonify({"success": False, "error": "Campos obrigatórios em falta"}), 400
        
        # Validação de formato de email
        import re
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({"success": False, "error": "Formato de email inválido"}), 400
        
        # Obter template de email
        from email_templates.transactional_emails import get_email_confirmacao_consulta
        subject, html_content = get_email_confirmacao_consulta(nome, assunto)
        
        # Configurar destinatários
        recipients = [{"email": email, "name": nome}]
        bcc = [{"email": "samuelrolo@gmail.com", "name": "Samuel Rolo"}]
        
        # Preparar email de confirmação para o cliente
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=recipients,
            bcc=bcc,
            sender=BREVO_SENDER,
            subject=subject,
            html_content=html_content
        )
        
        # Enviar email via Brevo
        try:
            get_brevo_api().send_transac_email(send_smtp_email)
            logger.info(f"Email de confirmação enviado para {email}")
        except ApiException as e:
            logger.error(f"Erro ao enviar email via Brevo: {str(e)}")
            return jsonify({"success": False, "error": "Erro ao enviar email de confirmação"}), 500
        
        # Enviar email de notificação para o admin com os detalhes do pedido
        admin_subject = f"Novo Pedido de Consulta: {assunto}"
        admin_content = f"""
        <html><body style="font-family: Arial, sans-serif;">
            <h2 style="color: #BF9A33;">Novo Pedido de Consulta</h2>
            <p><strong>Nome:</strong> {nome}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Assunto:</strong> {assunto}</p>
            <p><strong>Mensagem:</strong></p>
            <div style="background: #f4f4f4; padding: 15px; border-left: 3px solid #BF9A33;">
                {mensagem.replace(chr(10), '<br>')}
            </div>
            <p style="margin-top: 20px; color: #666;">Recebido em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
        </body></html>
        """
        
        admin_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": "samuelrolo@gmail.com", "name": "Samuel Rolo"}],
            sender=BREVO_SENDER,
            subject=admin_subject,
            html_content=admin_content,
            reply_to={"email": email, "name": nome}
        )
        
        try:
            get_brevo_api().send_transac_email(admin_email)
            logger.info("Email de notificação enviado para o admin")
        except ApiException as e:
            logger.warning(f"Erro ao enviar notificação para admin: {str(e)}")
            # Não falhar o request se apenas a notificação falhar
        
        return jsonify({"success": True, "message": "Pedido enviado com sucesso"}), 200
        
    except Exception as e:
        logger.error(f"Erro ao processar pedido de consulta: {str(e)}")
        return jsonify({"success": False, "error": "Erro ao processar o pedido"}), 500
