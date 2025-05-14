# /home/ubuntu/share2inspire_backend/src/routes/payment.py

import os
import requests
import hmac
import hashlib
from flask import Blueprint, request, jsonify
import re
from dotenv import load_dotenv

# Constants
MBWAY_DESCRIPTION_FORMAT = "Pagamento Share2Inspire {order_id}"

# Importar função de envio de email (assumindo que será refatorada ou importada)
# from ..utils.email import send_brevo_email # Exemplo de importação futura

# Carregar variáveis de ambiente
load_dotenv()

payment_bp = Blueprint("payment", __name__, url_prefix="/api/payment")

# Chaves Ifthenpay (lidas do ambiente)
IFTHENPAY_MB_KEY = os.getenv("IFTHENPAY_MB_KEY")
IFTHENPAY_MBWAY_KEY = os.getenv("IFTHENPAY_MBWAY_KEY")
IFTHENPAY_PAYSHOP_KEY = os.getenv("IFTHENPAY_PAYSHOP_KEY")
IFTHENPAY_CALLBACK_KEY = os.getenv("IFTHENPAY_CALLBACK_KEY") # Chave para validar callbacks

# URL base da API Ifthenpay (verificar documentação se existe ambiente de teste)
IFTHENPAY_API_URL = "https://ifthenpay.com/api/" # Exemplo, confirmar URL correta

# Utility function to validate phone number format
def is_valid_phone_number(phone_number):
    # Example regex for validating phone numbers (adjust as needed)
    phone_regex = r"^\+?[1-9]\d{1,14}$"
    return re.match(phone_regex, phone_number) is not None

# --- Endpoint para Iniciar Pagamento --- #
@payment_bp.route("/initiate", methods=["POST"])
def initiate_payment():
    data = request.get_json()
    if not data:
        return jsonify({"erro": "Nenhum dado recebido"}), 400

    payment_method = data.get("paymentMethod")
    order_id = data.get("orderId") # ID único da sua encomenda/agendamento
    amount = data.get("amount")
    customer_name = data.get("customerName")
    customer_email = data.get("customerEmail")
    customer_phone = data.get("customerPhone") # Necessário para MBWAY

    if not all([payment_method, order_id, amount]):
        return jsonify({"erro": "Dados insuficientes para iniciar pagamento (método, ID da encomenda, valor)"}), 400

    headers = {"Content-Type": "application/json"}
    payload = {
        "order_id": str(order_id),
        "amount": str(amount),
        # Adicionar mais detalhes se a API Ifthenpay permitir/exigir
    }

    try:
        if payment_method == "mb":
            if not IFTHENPAY_MB_KEY:
                return jsonify({"erro": "Chave Multibanco não configurada no servidor."}), 500
            payload["mbKey"] = IFTHENPAY_MB_KEY
            # Adicionar validade se necessário: payload["expiry_days"] = "3"
            response = requests.post(f"{IFTHENPAY_API_URL}multibanco/references/init", json=payload, headers=headers)
            response.raise_for_status() # Lança erro para códigos HTTP >= 400
            payment_data = response.json()
            if payment_data.get("Status") == "0": # Verificar código de sucesso na doc
                return jsonify({
                    "message": "Referência Multibanco gerada com sucesso.",
                    "method": "mb",
                    "entity": payment_data.get("Entity"),
                    "reference": payment_data.get("Reference"),
                    "amount": payment_data.get("Amount"),
                    "expiryDate": payment_data.get("ExpiryDate") # Verificar nome do campo na doc
                }), 200
            else:
return jsonify({"erro": f"Erro ao gerar referência Multibanco: {payment_data.get('Message', 'Erro desconhecido')}"}), 500

        elif payment_method == "mbway":
             # 1. Verificar se a chave MBWAY está configurada
            if not IFTHENPAY_MBWAY_KEY:
                return jsonify({"erro": "Chave MB WAY não configurada no servidor."}), 500
            # 2. Validar o número de telemóvel
            if not customer_phone or not is_valid_phone_number(customer_phone):
                 return jsonify({"erro": "Número de telemóvel é obrigatório e deve ser válido para MB WAY."}), 400
             # 3. Preparar o payload específico para MBWAY
            payload["mbwayKey"] = IFTHENPAY_MBWAY_KEY
            payload["phone_number"] = str(customer_phone) # Garante que é string
            payload["description"] = MBWAY_DESCRIPTION_FORMAT.format(order_id=order_id)
            # 4. Fazer a chamada à API (uma única vez com o payload completo)
            # Confirme o endpoint exato na documentação da Ifthenpay
            response = requests.post(f"{IFTHENPAY_API_URL}mbway/request", json=payload, headers=headers)
            response.raise_for_status() # Lança erro para códigos HTTP >= 400
            payment_data = response.json()
            # 5. Processar a resposta
            if payment_data.get("Status") == "0": # Verificar código de sucesso na documentação
                return jsonify({
                    "message": "Pedido de pagamento MB WAY iniciado com sucesso. Aguarde confirmação na app.",
                    "method": "mbway",
                    "requestId": payment_data.get("RequestId") # ID do pedido MBWAY
                }), 200
            else:
                # Use aspas simples dentro da f-string para o .get() se a f-string usa aspas duplas
                return jsonify({"erro": f"Erro ao iniciar pagamento MB WAY: {payment_data.get('Message', 'Erro desconhecido')}"}), 500
     
        elif payment_method == "payshop":
            if not IFTHENPAY_PAYSHOP_KEY:
                return jsonify({"erro": "Chave Payshop não configurada no servidor."}), 500
            payload["payshopKey"] = IFTHENPAY_PAYSHOP_KEY
            # Adicionar validade se necessário: payload["validade"] = "3"
            response = requests.post(f"{IFTHENPAY_API_URL}payshop/references/init", json=payload, headers=headers) # Confirmar endpoint
            response.raise_for_status()
            payment_data = response.json()
            if payment_data.get("Status") == "0":
                return jsonify({
                    "message": "Referência Payshop gerada com sucesso.",
                    "method": "payshop",
                    "reference": payment_data.get("Reference"),
                    "amount": payment_data.get("Amount"),
                    "expiryDate": payment_data.get("ExpiryDate") # Verificar nome do campo
                }), 200
            else:
                return jsonify({"erro": f"Erro ao gerar referência Payshop: {payment_data.get('Message', 'Erro desconhecido')}"}), 500

        else:
            # Incluir aqui lógica para "revolut" e "bank-transfer" se forem processados pelo backend
            # Caso contrário, são tratados no frontend como instruções
            return jsonify({"erro": "Método de pagamento não suportado ou inválido"}), 400

    except requests.exceptions.RequestException as e:
        print(f"Erro de comunicação com a API Ifthenpay: {e}")
        return jsonify({"erro": "Não foi possível comunicar com o sistema de pagamentos. Tente novamente mais tarde."}), 503
    except Exception as e:
        print(f"Erro inesperado ao iniciar pagamento: {e}")
        return jsonify({"erro": "Ocorreu um erro inesperado no servidor."}), 500

# --- Endpoint para Callback Ifthenpay --- #
# NOTA: A Ifthenpay pode usar método GET com parâmetros na URL.
# É CRUCIAL verificar a documentação para o formato exato e método (GET/POST).
@payment_bp.route("/callback", methods=["GET", "POST"]) # Ajustar métodos conforme documentação
def payment_callback():
    print("Callback Ifthenpay recebido!")

    # 1. Obter dados (ajustar se for GET - request.args)
    if request.method == "POST":
        data = request.get_json()
        print("Dados Callback (POST):", data)
    else: # GET
        data = request.args
        print("Dados Callback (GET):", data)

    if not data:
        print("Callback Ifthenpay: Nenhum dado recebido.")
        return jsonify({"erro": "Nenhum dado recebido"}), 400

    # 2. Validar a origem do Callback (MUITO IMPORTANTE!)
    # A Ifthenpay geralmente envia uma chave ou assinatura para validar.
    # Exemplo hipotético usando uma chave partilhada (VERIFICAR DOCUMENTAÇÃO!)
    chave_recebida = data.get("chave") # Nome do parâmetro/campo da chave na doc
    if not IFTHENPAY_CALLBACK_KEY or not chave_recebida or chave_recebida != IFTHENPAY_CALLBACK_KEY:
        print("Callback Ifthenpay: Chave de validação inválida ou em falta!")
        # Não retornar erro detalhado para evitar dar pistas a atacantes
        return jsonify({"erro": "Pedido inválido"}), 403 # Forbidden

    # 3. Processar os dados do callback
    order_id = data.get("order_id") # Ou o nome do campo que identifica a encomenda
    payment_status = data.get("status") # Ou o nome do campo do estado
    amount_paid = data.get("valor") # Ou o nome do campo do valor
    payment_method_used = data.get("metodo") # Ou o nome do campo do método
    # ... outros campos relevantes

    if not order_id or not payment_status:
        print("Callback Ifthenpay: Dados essenciais em falta (ID encomenda, estado)")
        return jsonify({"erro": "Dados incompletos"}), 400

    # 4. Lógica de Negócio Pós-Pagamento
    if payment_status == "PAGO": # Verificar valor exato do estado na doc
        print(f"Pagamento confirmado para encomenda {order_id}, Valor: {amount_paid}, Método: {payment_method_used}")

        # TODO: Adicionar lógica para marcar a encomenda/agendamento como paga na sua base de dados (se aplicável)

        # Enviar email de confirmação para o admin (srshare2inspire@gmail.com)
        try:
            # Obter detalhes do cliente (email, nome) associados ao order_id (pode precisar de DB)
            customer_email_placeholder = "email_cliente@exemplo.com" # Substituir por email real
            customer_name_placeholder = "Nome Cliente" # Substituir por nome real
            booking_details_placeholder = f"Detalhes do agendamento para {order_id}" # Obter detalhes reais

            # Usar a função de envio de email (refatorada)
            # send_brevo_email(
            #     to_email="srshare2inspire@gmail.com",
            #     to_name="Share2Inspire Admin",
            #     subject=f"Confirmação de Pagamento - Encomenda {order_id}",
            #     html_content=f"<p>Pagamento confirmado para a encomenda {order_id}.</p><p>Valor: {amount_paid}</p><p>Método: {payment_method_used}</p><p>Cliente: {customer_name_placeholder} ({customer_email_placeholder})</p><p>Detalhes: {booking_details_placeholder}</p>"
            # )
            print(f"SUCESSO: Email de confirmação para admin (encomenda {order_id}) seria enviado aqui.")

            # Opcional: Enviar email de confirmação para o cliente
            # send_brevo_email(
            #     to_email=customer_email_placeholder,
            #     to_name=customer_name_placeholder,
            #     subject=f"Confirmação do seu Agendamento Share2Inspire (Ref: {order_id})",
            #     html_content=f"<p>Olá {customer_name_placeholder},</p><p>Confirmamos o pagamento do seu agendamento (Ref: {order_id}).</p><p>Detalhes: {booking_details_placeholder}</p><p>Obrigado!</p>"
            # )
            # print(f"SUCESSO: Email de confirmação para cliente {customer_email_placeholder} (encomenda {order_id}) seria enviado aqui.")

        except Exception as email_error:
            print(f"ERRO ao enviar email de confirmação pós-pagamento para encomenda {order_id}: {email_error}")
            # Considerar logar este erro de forma mais persistente

        # Responder à Ifthenpay que o callback foi processado com sucesso
        # A resposta exata depende da documentação (pode ser vazio, um JSON específico, etc.)
        return jsonify({"status": "OK", "message": "Callback processado com sucesso."}) # Exemplo

    else:
        # Lidar com outros estados (ex: CANCELADO, FALHADO)
        print(f"Callback recebido para encomenda {order_id} com estado: {payment_status}")
        return jsonify({"status": "OK", "message": f"Callback recebido para estado {payment_status}."}) # Exemplo

    # Se chegou aqui, algo correu mal no processamento interno
    return jsonify({"erro": "Erro interno no processamento do callback"}), 500

# TODO: Refatorar a lógica de envio de email Brevo para um módulo utilitário
# Exemplo: src/utils/email.py
# def send_brevo_email(to_email, to_name, subject, html_content):
#     # ... (código de configuração e envio Brevo aqui)

