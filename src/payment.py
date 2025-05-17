# /home/ubuntu/share2inspire_backend/src/routes/payment.py

import os
import requests
import hmac
import hashlib
import json
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

payment_bp = Blueprint("payment", __name__, url_prefix="/api/payment")

# Chaves Ifthenpay (lidas do ambiente)
IFTHENPAY_MB_KEY = os.getenv("IFTHENPAY_MB_KEY")
IFTHENPAY_MBWAY_KEY = os.getenv("IFTHENPAY_MBWAY_KEY")
IFTHENPAY_PAYSHOP_KEY = os.getenv("IFTHENPAY_PAYSHOP_KEY")
IFTHENPAY_CALLBACK_KEY = os.getenv("IFTHENPAY_CALLBACK_KEY")
IFTHENPAY_ANTI_PHISHING_KEY = os.getenv("ANTI_PHISHING_KEY")

# URL base da API Ifthenpay
IFTHENPAY_API_URL = "https://ifthenpay.com/api/"

# --- Endpoint para Iniciar Pagamento --- #
@payment_bp.route("/initiate", methods=["POST"])
def initiate_payment():
    """
    Endpoint para iniciar um pagamento com Ifthenpay.
    Suporta métodos: MB (Multibanco), MBWAY, Payshop
    """
    print("Endpoint /api/payment/initiate chamado com método POST")
    data = request.get_json()
    print(f"Dados recebidos: {json.dumps(data, indent=2)}")
    
    if not data:
        print("Erro: Nenhum dado recebido no corpo da requisição")
        return jsonify({"error": "Nenhum dado recebido"}), 400

    payment_method = data.get("paymentMethod")
    order_id = data.get("orderId")  # ID único da encomenda/agendamento
    amount = data.get("amount")
    customer_name = data.get("customerName")
    customer_email = data.get("customerEmail")
    customer_phone = data.get("customerPhone")  # Necessário para MBWAY

    print(f"Método: {payment_method}, ID: {order_id}, Valor: {amount}, Cliente: {customer_name}")

    if not all([payment_method, order_id, amount]):
        print("Erro: Dados insuficientes para iniciar pagamento")
        return jsonify({"error": "Dados insuficientes para iniciar pagamento (método, ID da encomenda, valor)"}), 400

    headers = {"Content-Type": "application/json"}

    try:
        # Processamento para Multibanco
        if payment_method == "mb":
            if not IFTHENPAY_MB_KEY:
                print("Erro: Chave Multibanco não configurada")
                return jsonify({"error": "Chave Multibanco não configurada no servidor."}), 500
            
            print("Iniciando pagamento Multibanco")
            payload = {
                "mbKey": IFTHENPAY_MB_KEY,
                "orderId": str(order_id),
                "amount": str(amount),
                "description": f"Pagamento Share2Inspire {order_id}"
            }
            
            response = requests.post(f"{IFTHENPAY_API_URL}multibanco/references", json=payload, headers=headers)
            response.raise_for_status()
            payment_data = response.json()
            
            print(f"Resposta Multibanco: {json.dumps(payment_data, indent=2)}")
            
            if payment_data.get("Status") == "0":
                return jsonify({
                    "success": True,
                    "message": "Referência Multibanco gerada com sucesso.",
                    "method": "mb",
                    "entity": payment_data.get("Entity"),
                    "reference": payment_data.get("Reference"),
                    "amount": payment_data.get("Amount"),
                    "expiryDate": payment_data.get("ExpiryDate")
                }), 200
            else:
                error_message = payment_data.get("Message", "Erro desconhecido")
                print(f"Erro Multibanco: {error_message}")
                return jsonify({"error": f"Erro ao gerar referência Multibanco: {error_message}"}), 500
        
        # Processamento para MB WAY
        elif payment_method == "mbway":
            if not IFTHENPAY_MBWAY_KEY:
                print("Erro: Chave MB WAY não configurada")
                return jsonify({"error": "Chave MB WAY não configurada no servidor."}), 500
            
            if not customer_phone:
                print("Erro: Número de telemóvel obrigatório para MB WAY")
                return jsonify({"error": "Número de telemóvel é obrigatório para MB WAY."}), 400
            
            print("Iniciando pagamento MB WAY")
            payload = {
                "mbwayKey": IFTHENPAY_MBWAY_KEY,
                "orderId": str(order_id),
                "amount": str(amount),
                "phone": str(customer_phone),
                "description": f"Pagamento Share2Inspire {order_id}"
            }
            
            response = requests.post(f"{IFTHENPAY_API_URL}mbway/payment", json=payload, headers=headers)
            response.raise_for_status()
            payment_data = response.json()
            
            print(f"Resposta MB WAY: {json.dumps(payment_data, indent=2)}")
            
            if payment_data.get("Status") == "0":
                return jsonify({
                    "success": True,
                    "message": "Pedido de pagamento MB WAY iniciado com sucesso. Aguarde confirmação na app.",
                    "method": "mbway",
                    "idPedido": payment_data.get("IdPedido"),
                    "referencia": payment_data.get("Referencia"),
                    "amount": amount
                }), 200
            else:
                error_message = payment_data.get("Message", "Erro desconhecido")
                print(f"Erro MB WAY: {error_message}")
                return jsonify({"error": f"Erro ao iniciar pagamento MB WAY: {error_message}"}), 500
        
        # Processamento para Payshop
        elif payment_method == "payshop":
            if not IFTHENPAY_PAYSHOP_KEY:
                print("Erro: Chave Payshop não configurada")
                return jsonify({"error": "Chave Payshop não configurada no servidor."}), 500
            
            print("Iniciando pagamento Payshop")
            payload = {
                "payshopKey": IFTHENPAY_PAYSHOP_KEY,
                "orderId": str(order_id),
                "amount": str(amount),
                "description": f"Pagamento Share2Inspire {order_id}"
            }
            
            response = requests.post(f"{IFTHENPAY_API_URL}payshop/references", json=payload, headers=headers)
            response.raise_for_status()
            payment_data = response.json()
            
            print(f"Resposta Payshop: {json.dumps(payment_data, indent=2)}")
            
            if payment_data.get("Status") == "0":
                return jsonify({
                    "success": True,
                    "message": "Referência Payshop gerada com sucesso.",
                    "method": "payshop",
                    "reference": payment_data.get("Reference"),
                    "amount": payment_data.get("Amount"),
                    "expiryDate": payment_data.get("ExpiryDate")
                }), 200
            else:
                error_message = payment_data.get("Message", "Erro desconhecido")
                print(f"Erro Payshop: {error_message}")
                return jsonify({"error": f"Erro ao gerar referência Payshop: {error_message}"}), 500
        
        else:
            print(f"Método de pagamento não suportado: {payment_method}")
            return jsonify({"error": "Método de pagamento não suportado ou inválido"}), 400

    except requests.exceptions.RequestException as e:
        print(f"Erro de comunicação com a API Ifthenpay: {e}")
        return jsonify({"error": "Não foi possível comunicar com o sistema de pagamentos. Tente novamente mais tarde."}), 503
    except Exception as e:
        print(f"Erro inesperado ao iniciar pagamento: {e}")
        return jsonify({"error": "Ocorreu um erro inesperado no servidor."}), 500

# --- Endpoint para Callback Ifthenpay --- #
@payment_bp.route("/callback", methods=["GET", "POST"])
def payment_callback():
    """
    Endpoint para receber callbacks da Ifthenpay quando um pagamento é processado.
    Suporta tanto GET (para Multibanco) quanto POST (para MB WAY)
    """
    print("Callback Ifthenpay recebido!")

    # Obter dados conforme o método HTTP
    if request.method == "POST":
        data = request.get_json()
        print("Dados Callback (POST):", data)
    else:  # GET
        data = request.args.to_dict()
        print("Dados Callback (GET):", data)

    if not data:
        print("Callback Ifthenpay: Nenhum dado recebido.")
        return jsonify({"error": "Nenhum dado recebido"}), 400

    # Validar a origem do Callback usando a chave anti-phishing
    anti_phishing = data.get("phishingkey")
    if not IFTHENPAY_ANTI_PHISHING_KEY or not anti_phishing or anti_phishing != IFTHENPAY_ANTI_PHISHING_KEY:
        print("Callback Ifthenpay: Chave anti-phishing inválida ou em falta!")
        return jsonify({"error": "Pedido inválido"}), 403  # Forbidden

    # Extrair dados do callback
    payment_method = data.get("payment_type")
    order_id = data.get("order_id") or data.get("orderId")
    payment_status = data.get("status")
    amount = data.get("amount") or data.get("valor")
    
    if not order_id or not payment_status:
        print("Callback Ifthenpay: Dados essenciais em falta (ID encomenda, estado)")
        return jsonify({"error": "Dados incompletos"}), 400

    # Processar o pagamento conforme o status
    if payment_status == "paid" or payment_status == "confirmed":
        print(f"Pagamento confirmado para encomenda {order_id}, Valor: {amount}, Método: {payment_method}")
        
        # TODO: Atualizar o status do pagamento na base de dados
        # TODO: Enviar email de confirmação para o cliente e para o admin
        
        # Responder à Ifthenpay que o callback foi processado com sucesso
        return jsonify({"status": "OK", "message": "Callback processado com sucesso."})
    else:
        print(f"Callback recebido para encomenda {order_id} com estado: {payment_status}")
        return jsonify({"status": "OK", "message": f"Callback recebido para estado {payment_status}."})

# --- Endpoint para Verificar Status de Pagamento --- #
@payment_bp.route("/status/<order_id>", methods=["GET"])
def check_payment_status(order_id):
    """
    Endpoint para verificar o status de um pagamento
    """
    print(f"Verificando status do pagamento para ordem: {order_id}")
    
    # TODO: Implementar verificação real do status na base de dados
    # Por enquanto, retornamos um status fictício
    
    return jsonify({
        "orderId": order_id,
        "status": "pending",  # Valores possíveis: pending, paid, cancelled, expired
        "message": "Pagamento pendente"
    })
