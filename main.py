# main.py para a raiz do projeto
import os
from src.main import app

# Imprimir todas as variáveis de ambiente para diagnóstico
print("=== VARIÁVEIS DE AMBIENTE DISPONÍVEIS ===")
for key in ["BREVO_API_KEY", "IFTHENPAY_GATEWAY_KEY", "IFTHENPAY_CALLBACK_KEY", 
           "IFTHENPAY_MBWAY_KEY", "IFTHENPAY_PAYSHOP_KEY", "IFTHENPAY_MB_KEY", 
           "FLASK_SECRET_KEY", "ANTI_PHISHING_KEY"]:
    print(f"{key}: {'DEFINIDA' if os.getenv(key) else 'NÃO DEFINIDA'}")

# Isto é necessário para o App Engine encontrar a aplicação
if __name__ == "__main__":
    app.run()
