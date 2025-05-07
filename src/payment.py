# /home/ubuntu/share2inspire_Backend/src/routes/payment.py

import os
import requests
from flask import Blueprint, request, jsonify, current_app
from dotenv import load_dotenv

# Importar função de envio de email do novo módulo de utilitários
from ..utils.email_service import send_brevo_email

# Carregar variáveis de ambiente
load_dotenv()

payment_bp = Blueprint("payment", __name__, url_prefix="/api/payment")

# Chaves Ifthenpay (lidas do ambiente)
IFTHENPAY_GATEWAY_KEY = os.getenv("IFTHENPAY_GATEWAY_KEY", "3532-9893-7426-5310") # Chave Backoffice confirmada pelo utilizador
IFTHENPAY_CALLBACK_KEY = os.getenv("IFTHENPAY_CALLBACK_KEY") # Chave para validar callbacks

# URL base da API Ifthenpay para Pay By Link
IFTHENPAY_API_BASE_URL = "https://api.ifthenpay.com/gateway"

# Detalhes do E-book (poderiam vir de uma configuração ou base de dados)
EBOOK_ID = "GESTAO_MUDANCA_01"
EBOOK_NAME = "GESTÃO DA MUDANÇA"
EBOOK_PRICE = "7.50"
EBOOK_FILE_PATH = "/home/ubuntu/upload/Samuel Rolo - Gestão da Mudança - maio 2025.pdf" # Caminho para o ficheiro do e-book
EBOOK_ATTACHMENT_NAME = "Samuel Rolo - Gestão da Mudança.pdf"

# --- Endpoint para Iniciar Pagamento do E-book --- #
@payment_bp.route("/initiate-ebook-payment", methods=["POST"])
def initiate_ebook_payment():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Nenhum dado recebido"}), 400

    order_id = data.get("order_id", f"EBOOK_{EBOOK_ID}_{os.urandom(4).hex()}") # Gerar um ID de encomenda único
    amount = EBOOK_PRICE
    description = f"Compra do E-book: {EBOOK_NAME}"
    customer_name = data.get("customer_name")
    customer_email = data.get("customer_email")

    # URLs de redirecionamento (devem ser URLs absolutos do seu frontend)
    # Estes são exemplos, ajuste para os URLs corretos da sua aplicação frontend
    base_frontend_url = request.host_url.replace("http://", "https://") # Tenta usar HTTPS
    if "127.0.0.1" in base_frontend_url or "localhost" in base_frontend_url:
        base_frontend_url = "http://localhost:PORTA_DO_SEU_FRONTEND/" # Ajuste se necessário para dev
    
    success_url = data.get("success_url", base_frontend_url + "loja/pagamento-sucesso.html")
    error_url = data.get("error_url", base_frontend_url + "loja/pagamento-erro.html")
    cancel_url = data.get("cancel_url", base_frontend_url + "loja/gestao-da-mudanca/index.html")

    if not all([customer_name, customer_email]):
        return jsonify({"error": "Dados insuficientes: nome e e-mail do cliente são obrigatórios."}), 400

    if not IFTHENPAY_GATEWAY_KEY:
        current_app.logger.error("IFTHENPAY_GATEWAY_KEY não está configurada no servidor.")
        return jsonify({"error": "Configuração de pagamento em falta no servidor."}), 500

    headers = {"Content-Type": "application/json"}
    payload = {
        "id": str(order_id),
        "amount": str(amount),
        "description": description,
        "accounts": "MBWAY;MB;PAYSHOP;CCARD", # Permitir vários métodos comuns
        "success_url": success_url,
        "error_url": error_url,
        "cancel_url": cancel_url,
        "lang": "pt",
        # Guardar dados do cliente para usar no callback (idealmente numa DB temporária ou sessão)
        # Por simplicidade, vamos assumir que o order_id pode ser usado para recuperar isto depois
        # Ou que a ifthenpay permite passar dados customizados que são retornados no callback
        "custom_fields": {
            "customer_email": customer_email,
            "customer_name": customer_name,
            "product_id": EBOOK_ID
        }
    }

    # Guardar temporariamente os dados do cliente associados ao order_id
    # Em produção, usar uma base de dados ou um sistema de cache como Redis
    if not hasattr(current_app, 'pending_orders'):
        current_app.pending_orders = {}
    current_app.pending_orders[str(order_id)] = {
        "customer_email": customer_email,
        "customer_name": customer_name,
        "product_id": EBOOK_ID,
        "amount": amount
    }
    current_app.logger.info(f"Pedido de pagamento iniciado: {order_id}, Cliente: {customer_email}")

    try:
        api_url = f"{IFTHENPAY_API_BASE_URL}/pinpay/{IFTHENPAY_GATEWAY_KEY}"
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        payment_data = response.json()

        if payment_data.get("PinCode") and payment_data.get("RedirectUrl"):
            current_app.logger.info(f"Link de pagamento gerado para {order_id}: {payment_data.get('RedirectUrl')}")
            return jsonify({
                "message": "Link de pagamento gerado com sucesso.",
                "redirectUrl": payment_data.get("RedirectUrl"),
                "pinpayUrl": payment_data.get("PinpayUrl"),
                "pinCode": payment_data.get("PinCode"),
                "orderId": str(order_id)
            }), 200
        else:
            current_app.logger.error(f"Erro ao gerar link de pagamento ifthenpay: {payment_data}")
            return jsonify({"error": payment_data.get("message", "Erro desconhecido ao gerar link de pagamento ifthenpay.")}), 500

    except requests.exceptions.Timeout:
        current_app.logger.error(f"Timeout ao comunicar com a API Ifthenpay para {order_id}")
        return jsonify({"error": "O sistema de pagamentos demorou muito a responder. Tente novamente."}), 504
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Erro de comunicação com a API Ifthenpay para {order_id}: {e}")
        return jsonify({"error": "Não foi possível comunicar com o sistema de pagamentos. Tente novamente mais tarde."}), 503
    except Exception as e:
        current_app.logger.error(f"Erro inesperado ao iniciar pagamento para {order_id}: {e}")
        return jsonify({"error": "Ocorreu um erro inesperado no servidor."}), 500

# --- Endpoint para Callback Ifthenpay --- #
@payment_bp.route("/callback", methods=["GET", "POST"]) # Ifthenpay PayByLink usa GET para callback
def payment_callback():
    current_app.logger.info("Callback Ifthenpay recebido!")

    # PayByLink callback é GET
    data = request.args
    current_app.logger.info(f"Dados Callback (GET): {data}")

    if not data:
        current_app.logger.warning("Callback Ifthenpay: Nenhum dado recebido.")
        return jsonify({"error": "Nenhum dado recebido"}), 400

    # Validar a origem do Callback (MUITO IMPORTANTE!)
    # Para PayByLink, a validação é feita comparando a chave_anti_phishing (IFTHENPAY_CALLBACK_KEY)
    # com o valor recebido no parâmetro 'chave' do callback.
    chave_recebida = data.get("chave")
    id_transacao = data.get("id") # ID da transação ifthenpay
    order_id_callback = data.get("referencia") # A 'referencia' é o nosso 'order_id'/'id' enviado na criação do link
    valor_pago = data.get("valor")
    estado_pagamento = data.get("estado") # "PAGO", "FALHOU", "CANCELADO"

    if not IFTHENPAY_CALLBACK_KEY:
        current_app.logger.error("IFTHENPAY_CALLBACK_KEY não está configurada no servidor para validação do callback.")
        return jsonify({"error": "Configuração de segurança em falta"}), 500
        
    if not chave_recebida or chave_recebida != IFTHENPAY_CALLBACK_KEY:
        current_app.logger.warning(f"Callback Ifthenpay: Chave de validação inválida ou em falta. Recebida: '{chave_recebida}'")
        return jsonify({"error": "Pedido inválido"}), 403

    if not order_id_callback or not estado_pagamento:
        current_app.logger.warning(f"Callback Ifthenpay: Dados essenciais em falta (referencia/order_id, estado). ID Trans: {id_transacao}")
        return jsonify({"error": "Dados incompletos"}), 400

    # Recuperar dados do cliente guardados temporariamente
    pending_order_data = current_app.pending_orders.pop(str(order_id_callback), None) if hasattr(current_app, 'pending_orders') else None

    if not pending_order_data:
        current_app.logger.warning(f"Callback Ifthenpay: Encomenda {order_id_callback} não encontrada nos pedidos pendentes. Pode já ter sido processada ou é inválida.")
        # Mesmo que não encontre, responder OK à ifthenpay para não haver retries desnecessários se for um callback válido.
        return jsonify({"status": "OK", "message": "Callback recebido, encomenda não pendente."})

    customer_email = pending_order_data.get("customer_email")
    customer_name = pending_order_data.get("customer_name")
    product_id = pending_order_data.get("product_id")
    expected_amount = pending_order_data.get("amount")

    if estado_pagamento.upper() == "PAGO":
        current_app.logger.info(f"Pagamento CONFIRMADO para encomenda {order_id_callback} (Trans. ID: {id_transacao}), Valor: {valor_pago}, Cliente: {customer_email}")
        
        if str(valor_pago) != str(expected_amount):
            current_app.logger.error(f"ALERTA DE SEGURANÇA: Valor pago ({valor_pago}) diferente do esperado ({expected_amount}) para encomenda {order_id_callback}.")
            # Considerar não enviar o e-book e investigar
            return jsonify({"status": "OK", "message": "Callback processado, mas com discrepância de valor."})

        if product_id == EBOOK_ID:
            email_subject = f"O seu E-book: {EBOOK_NAME}"
            email_html_content = f"<h1>Olá {customer_name},</h1><p>Obrigado pela sua compra! Em anexo encontra o seu e-book '{EBOOK_NAME}'.</p><p>Esperamos que goste!</p><p>Com os melhores cumprimentos,<br>Samuel Rolo</p>"
            
            if not os.path.exists(EBOOK_FILE_PATH):
                current_app.logger.error(f"ERRO CRÍTICO: Ficheiro do e-book não encontrado em {EBOOK_FILE_PATH} para a encomenda {order_id_callback}.")
                # Notificar admin, mas não falhar o callback para ifthenpay
            else:
                email_sent = send_brevo_email(
                    to_email=customer_email,
                    to_name=customer_name,
                    subject=email_subject,
                    html_content=email_html_content,
                    attachment_path=EBOOK_FILE_PATH,
                    attachment_name=EBOOK_ATTACHMENT_NAME
                )
                if email_sent:
                    current_app.logger.info(f"E-book '{EBOOK_NAME}' enviado com sucesso para {customer_email} (Encomenda: {order_id_callback}).")
                else:
                    current_app.logger.error(f"Falha ao enviar e-book '{EBOOK_NAME}' para {customer_email} (Encomenda: {order_id_callback}). Verificar logs do email_service.")
        else:
            current_app.logger.warning(f"Produto desconhecido '{product_id}' para encomenda {order_id_callback}. Nenhum e-mail enviado.")

        # Responder à Ifthenpay que o callback foi processado com sucesso
        return jsonify({"status": "OK", "message": "Callback de pagamento PAGO processado com sucesso."})
    else:
        current_app.logger.info(f"Callback recebido para encomenda {order_id_callback} (Trans. ID: {id_transacao}) com estado: {estado_pagamento}. Valor: {valor_pago}")
        return jsonify({"status": "OK", "message": f"Callback recebido para estado {estado_pagamento}."})

    # Fallback, não deveria chegar aqui se a lógica acima estiver correta
    current_app.logger.error(f"Erro interno não esperado no processamento do callback para {order_id_callback}.")
    return jsonify({"error": "Erro interno no processamento do callback"}), 500

# Manter os endpoints antigos se ainda forem usados por outras partes do share2inspire_Backend
# Se não forem, podem ser removidos ou comentados.
# O código abaixo é o original de payment.py, para referência ou se precisar de ser mantido.

# IFTHENPAY_MB_KEY = os.getenv("IFTHENPAY_MB_KEY")
# IFTHENPAY_MBWAY_KEY = os.getenv("IFTHENPAY_MBWAY_KEY")
# IFTHENPAY_PAYSHOP_KEY = os.getenv("IFTHENPAY_PAYSHOP_KEY")
# IFTHENPAY_API_URL_LEGACY = "https://ifthenpay.com/api/" # Exemplo, confirmar URL correta

# @payment_bp.route("/initiate", methods=["POST"])
# def initiate_payment_legacy():
# ... (código original do /initiate que lidava com mb, mbway, payshop separadamente)

