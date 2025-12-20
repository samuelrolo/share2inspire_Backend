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
                <h2>Novo Pedido: {service_name} (Pendente Pagamento)</h2>
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <p><strong>Status Pagamento:</strong> Iniciado (MB WAY {amount}€)</p>
                    <p><strong>Referência Pedido:</strong> {payment_data['orderId']}</p>
                    <p><strong>Serviço:</strong> {service_name}</p>
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
            subject=f"{service_name} - {name} (Aguardar Pagamento)",
            html_content=email_content,
            reply_to={"email": email, "name": name},
            attachment=attachment if attachment else None
        )

        try:
            get_brevo_api().send_transac_email(send_smtp_email)
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
@services_bp.route("/send-report-email", methods=["POST"])
def send_report_email():
    try:
        data = request.get_json()
        print(f"Dados recebidos para email de relatório: {data}")
        
        if not data:
            return jsonify({"success": False, "error": "Dados não recebidos"}), 400
            
        email = data.get('email')
        name = data.get('name')
        report_data = data.get('reportData')
        
        if not email or not name or not report_data:
            return jsonify({"success": False, "error": "Dados obrigatórios em falta (Email, Nome, Dados do Relatório)"}), 400

        # E-mail Admin (rsshare2inspire@gmail.com conforme pedido do utilizador)
        ADMIN_EMAIL = "rsshare2inspire@gmail.com"
        
        # Gerar o conteúdo HTML do relatório (simplificado para o corpo do email ou link)
        # Por agora, vamos enviar os detalhes principais no corpo do email
        profile = report_data.get('candidate_profile', {})
        verdict = report_data.get('final_verdict', {})
        summary = report_data.get('executive_summary', {})
        
        email_html = f"""
        <html>
        <body style="font-family: 'Poppins', Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                <!-- Header -->
                <div style="text-align: center; padding: 40px 20px; background-color: #ffffff;">
                    <img src="https://share2inspire.pt/images/logo.png" alt="Share2Inspire" style="max-width: 200px; height: auto;">
                    <h1 style="color: #BF9A33; font-size: 24px; margin-top: 25px; font-weight: 700; letter-spacing: 1px;">Relatório de Análise de CV</h1>
                </div>
                
                <!-- Body -->
                <div style="padding: 0 40px 40px 40px;">
                    <p style="font-size: 16px;">Olá <strong>{name}</strong>,</p>
                    
                    <p style="font-size: 15px; color: #555;">Obrigado por confiares na Share2Inspire para analisar o teu percurso profissional.</p>
                    
                    <p style="font-size: 15px; color: #555;">Em anexo, encontras o Relatório Completo de Análise de CV em PDF, onde aprofundamos a leitura estratégica do teu perfil, indo além da síntese apresentada no ecrã. Este documento detalha posicionamento, maturidade profissional, potencial de mercado e recomendações concretas para evolução.</p>
                    
                    <p style="font-size: 15px; color: #555;">A análise confirma um perfil de elevada senioridade, com forte alinhamento a funções de liderança estratégica em Transformação Digital, RH e Futuro do Trabalho. Mais do que um CV sólido, estamos perante uma narrativa profissional com potencial de diferenciação clara no mercado global.</p>
                    
                    <div style="margin-top: 35px; border-top: 1px solid #eee; padding-top: 30px;">
                        <h3 style="color: #1a1a1a; font-size: 18px; margin-bottom: 20px; border-left: 4px solid #BF9A33; padding-left: 15px;">Próximos passos recomendados</h3>
                        
                        <!-- Kickstart Pro -->
                        <div style="margin-bottom: 30px;">
                            <h4 style="color: #BF9A33; margin-bottom: 10px; font-size: 16px;">1. Sessão estratégica Kickstart Pro</h4>
                            <p style="font-size: 14px; color: #666; margin-bottom: 15px;">Uma sessão individual de follow up, focada em transformar insights em decisões concretas. Trabalhamos posicionamento, foco estratégico e próximos movimentos de carreira, com abordagem prática e orientada a impacto.</p>
                            <a href="https://share2inspire.pt/pages/servicos.html#kickstart" style="display: inline-block; background-color: #BF9A33; color: white; padding: 12px 25px; text-decoration: none; border-radius: 50px; font-weight: 600; font-size: 14px;">👉 Agendar Kickstart Pro</a>
                        </div>
                        
                        <!-- Revisão Profissional -->
                        <div>
                            <h4 style="color: #BF9A33; margin-bottom: 10px; font-size: 16px;">2. Revisão Profissional de CV</h4>
                            <p style="font-size: 14px; color: #666; margin-bottom: 15px;">Uma revisão aprofundada, humana e orientada a mercado, alinhando narrativa, estrutura e impacto do CV, tanto para leitura humana como para sistemas ATS.</p>
                            <a href="https://share2inspire.pt/pages/servicos.html#cv-review" style="display: inline-block; background-color: #1a1a1a; color: white; padding: 12px 25px; text-decoration: none; border-radius: 50px; font-weight: 600; font-size: 14px;">👉 Solicitar Revisão Profissional de CV</a>
                        </div>
                    </div>
                    
                    <p style="font-size: 14px; color: #888; margin-top: 40px;">Se preferires, podes também continuar a explorar o CV Analyzer, utilizando-o como ferramenta de diagnóstico contínuo.</p>
                    
                    <p style="font-size: 15px; color: #555; margin-top: 30px;">Estamos disponíveis para apoiar o próximo capítulo do teu percurso com clareza, estratégia e intenção.</p>
                </div>
                
                <!-- Footer -->
                <div style="background-color: #1a1a1a; color: #ffffff; padding: 40px 20px; text-align: center; border-radius: 0 0 12px 12px;">
                    <p style="font-size: 15px; font-weight: 600; margin-bottom: 5px;">Com estima,</p>
                    <p style="font-size: 16px; font-weight: 700; color: #BF9A33; margin: 0;">Equipa Share2Inspire</p>
                    <p style="font-size: 13px; opacity: 0.8; margin-top: 10px;">Human-Centred Career & Transformation Advisory</p>
                    <p style="font-size: 13px; margin-top: 20px;"><a href="https://share2inspire.pt" style="color: #BF9A33; text-decoration: none;">www.share2inspire.pt</a></p>
                    
                    <div style="margin-top: 30px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 20px; font-size: 11px; opacity: 0.6;">
                        <p>© 2025 Share2Inspire. Todos os direitos reservados.</p>
                        <p>Este é um envio automático, por favor não responda a este email.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": email, "name": name}],
            bcc=[{"email": ADMIN_EMAIL, "name": "Admin Share2Inspire"}],
            sender={"email": os.getenv("BREVO_SENDER_EMAIL", "srshare2inspire@gmail.com"), "name": "Share2Inspire Advisor"},
            subject=f"O seu Relatório de Análise CV | Próximos Passos Estratégicos - {name}",
            html_content=email_html
        )
        
        try:
            get_brevo_api().send_transac_email(send_smtp_email)
            return jsonify({"success": True, "message": "Relatório enviado por email com sucesso!"})
        except ApiException as e:
            print(f"Erro Brevo: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
            
    except Exception as e:
        print(f"Erro no endpoint send-report-email: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
