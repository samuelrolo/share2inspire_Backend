#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação principal do backend Share2Inspire - VERSÃO SIMPLIFICADA
Apenas com funcionalidades essenciais para Kickstart Pro
"""

import os
import logging
import requests
import json
from flask import Flask, jsonify, request
from flask_cors import CORS 
from dotenv import load_dotenv
from google.cloud import secretmanager
import google.generativeai as genai
from werkzeug.utils import secure_filename
import PyPDF2
import io

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Função para obter segredos do Google Secret Manager
def get_secret(secret_id):
    """Obter segredo do Google Secret Manager"""
    try:
        project_id = os.getenv('GCP_PROJECT_ID', 'share2inspire-beckend')
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode('UTF-8')
    except Exception as e:
        logger.warning(f"Não foi possível obter segredo {secret_id} do Secret Manager: {str(e)}")
        # Fallback para variável de ambiente
        return os.getenv(secret_id)

# Configurar Gemini API
GEMINI_API_KEY = get_secret('Gemini') or os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY não configurada")

# Criar aplicação Flask
app = Flask(__name__)

# Configuração CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "supports_credentials": True
    }
})

# Configurar chave secreta
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24).hex())

# Middleware global para garantir cabeçalhos CORS
@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Função para tratar preflight requests
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path=''):
    return jsonify({"success": True}), 200

# Rota principal
@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Share2Inspire Backend - Versão Simplificada",
        "version": "1.0.0"
    })

# === FUNCIONALIDADES BREVO (EMAIL) ===

def send_brevo_email(to_email, to_name, subject, html_content):
    """Enviar email via Brevo"""
    try:
        api_key = os.getenv('BREVO_API_KEY')
        sender_email = os.getenv('BREVO_SENDER_EMAIL')
        sender_name = os.getenv('BREVO_SENDER_NAME')
        
        if not all([api_key, sender_email, sender_name]):
            raise ValueError("Configurações Brevo em falta")
        
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json"
        }
        
        payload = {
            "sender": {
                "name": sender_name,
                "email": sender_email
            },
            "to": [
                {
                    "email": to_email,
                    "name": to_name
                }
            ],
            "subject": subject,
            "htmlContent": html_content
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        return {"success": True, "message": "Email enviado com sucesso"}
        
    except Exception as e:
        logger.error(f"Erro ao enviar email: {str(e)}")
        return {"success": False, "error": str(e)}

@app.route('/api/email/kickstart', methods=['POST'])
def send_kickstart_email():
    """Enviar email de confirmação do Kickstart Pro"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['customerName', 'customerEmail', 'customerPhone', 'appointmentDate', 'format', 'duration']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"success": False, "error": f"Campo obrigatório: {field}"}), 400
        
        # Preparar conteúdo do email
        subject = f"Confirmação de Agendamento - Kickstart Pro | {data['customerName']}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #bf9a33;">Novo Agendamento - Kickstart Pro</h2>
                
                <h3>Dados do Cliente:</h3>
                <ul>
                    <li><strong>Nome:</strong> {data['customerName']}</li>
                    <li><strong>Email:</strong> {data['customerEmail']}</li>
                    <li><strong>Telefone:</strong> {data['customerPhone']}</li>
                </ul>
                
                <h3>Detalhes da Sessão:</h3>
                <ul>
                    <li><strong>Data Preferencial:</strong> {data['appointmentDate']}</li>
                    <li><strong>Formato:</strong> {data['format']}</li>
                    <li><strong>Duração:</strong> {data['duration']}</li>
                    <li><strong>Preço:</strong> {data.get('amount', 'N/A')}€</li>
                </ul>
                
                <h3>Método de Pagamento:</h3>
                <p><strong>{data.get('paymentMethod', 'N/A')}</strong></p>
                
                {f"<p><strong>Telefone MB WAY:</strong> {data.get('mbwayPhone', 'N/A')}</p>" if data.get('mbwayPhone') else ""}
                
                <h3>Objetivos/Mensagem:</h3>
                <p>{data.get('message', 'Não especificado')}</p>
                
                <hr style="margin: 30px 0;">
                <p style="color: #666; font-size: 12px;">
                    Este email foi enviado automaticamente pelo sistema Share2Inspire.<br>
                    Data: {data.get('timestamp', 'N/A')}
                </p>
            </div>
        </body>
        </html>
        """
        
        # Enviar email
        result = send_brevo_email(
            to_email=os.getenv('BREVO_SENDER_EMAIL'),  # Enviar para si próprio
            to_name="Share2Inspire",
            subject=subject,
            html_content=html_content
        )
        
        if result['success']:
            logger.info(f"Email de Kickstart Pro enviado para {data['customerEmail']}")
            return jsonify({"success": True, "message": "Email enviado com sucesso"})
        else:
            return jsonify({"success": False, "error": result['error']}), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint de email: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# === FUNCIONALIDADES IFTHENPAY ===

def create_multibanco_payment(amount, order_id):
    """Criar pagamento Multibanco via Ifthenpay"""
    try:
        key = os.getenv('IFTHENPAY_MULTIBANCO_KEY')
        if not key:
            raise ValueError("Chave Multibanco não configurada")
        
        url = "https://ifthenpay.com/api/multibanco/reference"
        params = {
            'key': key,
            'amount': amount,
            'order_id': order_id
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return {
            "success": True,
            "entity": data.get('entity'),
            "reference": data.get('reference'),
            "amount": amount
        }
        
    except Exception as e:
        logger.error(f"Erro ao criar pagamento Multibanco: {str(e)}")
        return {"success": False, "error": str(e)}

def create_mbway_payment(amount, phone, order_id):
    """Criar pagamento MB WAY via Ifthenpay"""
    try:
        key = os.getenv('IFTHENPAY_MBWAY_KEY')
        if not key:
            raise ValueError("Chave MB WAY não configurada")
        
        url = "https://ifthenpay.com/api/mbway/payment"
        params = {
            'key': key,
            'amount': amount,
            'phone': phone,
            'order_id': order_id
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return {
            "success": True,
            "transaction_id": data.get('transaction_id'),
            "amount": amount,
            "phone": phone
        }
        
    except Exception as e:
        logger.error(f"Erro ao criar pagamento MB WAY: {str(e)}")
        return {"success": False, "error": str(e)}

def create_payshop_payment(amount, order_id):
    """Criar pagamento Payshop via Ifthenpay"""
    try:
        key = os.getenv('IFTHENPAY_PAYSHOP_KEY')
        if not key:
            raise ValueError("Chave Payshop não configurada")
        
        url = "https://ifthenpay.com/api/payshop/reference"
        params = {
            'key': key,
            'amount': amount,
            'order_id': order_id
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return {
            "success": True,
            "reference": data.get('reference'),
            "amount": amount
        }
        
    except Exception as e:
        logger.error(f"Erro ao criar pagamento Payshop: {str(e)}")
        return {"success": False, "error": str(e)}

@app.route('/api/ifthenpay/multibanco', methods=['POST'])
def process_multibanco_payment():
    """Processar pagamento Multibanco"""
    try:
        data = request.get_json()
        amount = data.get('amount')
        order_id = data.get('orderId')
        
        if not amount or not order_id:
            return jsonify({"success": False, "error": "Dados obrigatórios em falta"}), 400
        
        result = create_multibanco_payment(amount, order_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint Multibanco: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/ifthenpay/mbway', methods=['POST'])
def process_mbway_payment():
    """Processar pagamento MB WAY"""
    try:
        data = request.get_json()
        amount = data.get('amount')
        phone = data.get('phone')
        order_id = data.get('orderId')
        
        if not amount or not phone or not order_id:
            return jsonify({"success": False, "error": "Dados obrigatórios em falta"}), 400
        
        result = create_mbway_payment(amount, phone, order_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint MB WAY: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/ifthenpay/payshop', methods=['POST'])
def process_payshop_payment():
    """Processar pagamento Payshop"""
    try:
        data = request.get_json()
        amount = data.get('amount')
        order_id = data.get('orderId')
        
        if not amount or not order_id:
            return jsonify({"success": False, "error": "Dados obrigatórios em falta"}), 400
        
        result = create_payshop_payment(amount, order_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint Payshop: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# === FUNCIONALIDADES CANDIDATE FIT ===

def extract_text_from_pdf(pdf_file):
    """Extrair texto de um ficheiro PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        logger.error(f"Erro ao extrair texto do PDF: {str(e)}")
        return None

def analyze_cv_with_gemini(cv_text, job_description, seniority, country, sector):
    """Analisar CV com Gemini e gerar relatório"""
    try:
        if not GEMINI_API_KEY:
            return {"success": False, "error": "Gemini API não configurada"}
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
Você é um avaliador de candidaturas para carreiras corporativas, consultoria e áreas de transformação. 
Produz um diagnóstico claro, curto e acionável.

Contexto:
- Senioridade alvo: {seniority}
- País e mercado alvo: {country}
- Setor alvo: {sector}

Descrição da vaga:
{job_description}

Texto integral do CV:
{cv_text}

Gere um relatório Candidate Fit em formato JSON com a seguinte estrutura:
{{
  "score_global": <número 0-100>,
  "fit_band": "<Elevado|Moderado|Parcial>",
  "dimensões": {{
    "skills_técnicas": <número 0-100>,
    "experiência": <número 0-100>,
    "soft_skills": <número 0-100>,
    "fit_cultural": <número 0-100>,
    "educação": <número 0-100>
  }},
  "dim_state": {{
    "skills_técnicas": "<ok|warn|risk>",
    "experiência": "<ok|warn|risk>",
    "soft_skills": "<ok|warn|risk>",
    "fit_cultural": "<ok|warn|risk>",
    "educação": "<ok|warn|risk>"
  }},
  "dim_label": {{
    "skills_técnicas": "<Sólido|A reforçar|Crítico>",
    "experiência": "<Sólido|A reforçar|Crítico>",
    "soft_skills": "<Sólido|A reforçar|Crítico>",
    "fit_cultural": "<Sólido|A reforçar|Crítico>",
    "educação": "<Sólido|A reforçar|Crítico>"
  }},
  "pontos_fortes": ["...", "...", "..."],
  "lacunas": ["...", "...", "..."],
  "próximos_passos": ["...", "...", "..."],
  "resumo": "<3 linhas em linguagem executiva>"
}}

Dimensões e pesos:
- skills_técnicas: 40%
- experiência: 30%
- soft_skills: 15%
- fit_cultural: 10%
- educação: 5%

Regras:
- Avalia cada dimensão de 0 a 100
- Calcula score_global com os pesos acima
- Escreve pontos_fortes e lacunas de forma específica e não genérica
- Recomenda próximos_passos práticos para 30 dias
- Inclui um resumo em 3 linhas, linguagem executiva

Retorna APENAS o JSON, sem explicações adicionais.
"""
        
        response = model.generate_content(prompt)
        
        # Tentar extrair JSON da resposta
        response_text = response.text
        
        # Se a resposta contém markdown code blocks, remover
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0]
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0]
        
        report = json.loads(response_text.strip())
        return {"success": True, "report": report}
        
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao fazer parse do JSON da resposta Gemini: {str(e)}")
        return {"success": False, "error": "Erro ao processar resposta da análise"}
    except Exception as e:
        logger.error(f"Erro ao analisar CV com Gemini: {str(e)}")
        return {"success": False, "error": str(e)}

@app.route('/api/analyze_cv', methods=['POST'])
def analyze_cv():
    """Analisar CV e gerar relatório Candidate Fit"""
    try:
        # Verificar se é FormData ou JSON
        if 'file' in request.files:
            # Upload de ficheiro
            file = request.files['file']
            job_description = request.form.get('job_text', '')
            seniority = request.form.get('seniority', 'Mid')
            country = request.form.get('country', 'Portugal')
            sector = request.form.get('sector', 'Consultoria e Transformação')
            
            if file.filename == '':
                return jsonify({"success": False, "error": "Nenhum ficheiro selecionado"}), 400
            
            # Extrair texto do ficheiro
            if file.filename.endswith('.pdf'):
                cv_text = extract_text_from_pdf(file)
            else:
                cv_text = file.read().decode('utf-8')
            
            if not cv_text:
                return jsonify({"success": False, "error": "Não foi possível extrair texto do ficheiro"}), 400
        else:
            # JSON payload
            data = request.get_json()
            cv_text = data.get('cv_text', '')
            job_description = data.get('job_text', '')
            seniority = data.get('seniority', 'Mid')
            country = data.get('country', 'Portugal')
            sector = data.get('sector', 'Consultoria e Transformação')
            
            if not cv_text or not job_description:
                return jsonify({"success": False, "error": "CV e descrição da vaga são obrigatórios"}), 400
        
        # Analisar CV
        result = analyze_cv_with_gemini(cv_text, job_description, seniority, country, sector)
        
        if result['success']:
            logger.info(f"CV analisado com sucesso para senioridade: {seniority}")
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Erro no endpoint de análise de CV: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# === VERIFICAÇÃO DE SAÚDE ===

@app.route('/health')
def health_check():
    """Verificação de saúde do sistema"""
    return jsonify({
        "status": "healthy",
        "timestamp": "2025-07-07T12:00:00Z",
        "services": {
            "brevo": bool(os.getenv('BREVO_API_KEY')),
            "ifthenpay_multibanco": bool(os.getenv('IFTHENPAY_MULTIBANCO_KEY')),
            "ifthenpay_mbway": bool(os.getenv('IFTHENPAY_MBWAY_KEY')),
            "ifthenpay_payshop": bool(os.getenv('IFTHENPAY_PAYSHOP_KEY')),
            "gemini": bool(GEMINI_API_KEY)
        }
    })

# === TRATAMENTO DE ERROS ===

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Endpoint não encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Erro interno do servidor"}), 500

# === INICIALIZAÇÃO ===

if __name__ == '__main__':
    # Verificar variáveis de ambiente
    logger.info("=== VERIFICAÇÃO DE VARIÁVEIS DE AMBIENTE ===")
    
    env_vars = [
        'BREVO_API_KEY', 'BREVO_SENDER_EMAIL', 'BREVO_SENDER_NAME',
        'IFTHENPAY_MULTIBANCO_KEY', 'IFTHENPAY_MBWAY_KEY', 'IFTHENPAY_PAYSHOP_KEY'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "****"
            logger.info(f"{var}: DEFINIDA ({masked})")
        else:
            logger.warning(f"{var}: NÃO DEFINIDA")
    
    logger.info("=== BACKEND SHARE2INSPIRE INICIADO ===")
    
    # Executar aplicação
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

