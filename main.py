# main.py (na raiz do projeto)
import os
import logging
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Criar aplicação Flask
app = Flask(__name__)

# Configuração CORS melhorada para desenvolvimento e produção
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://share2inspire.pt",           # Domínio de produção
            "http://localhost:3000",              # Porta 3000 (comum para React/Node)
            "http://localhost:5000",              # Porta 5000 (comum para Flask)
            "http://localhost:5500",              # Porta 5500 (comum para Live Server no VS Code)
            "http://localhost:8080",              # Porta 8080 (comum para http-server)
            "http://127.0.0.1:3000",              # Alternativas com IP local
            "http://127.0.0.1:5000",
            "http://127.0.0.1:5500",
            "http://127.0.0.1:8080"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
    }
}, supports_credentials=True)

# Configurar chave secreta
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24).hex())

# Importar e registar blueprints
try:
    from src.routes.feedback import feedback_bp
    app.register_blueprint(feedback_bp)
    logger.info("Blueprint de feedback registado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de feedback: {str(e)}")

try:
    from src.routes.payment import payment_bp
    app.register_blueprint(payment_bp)
    logger.info("Blueprint de payment registado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar blueprint de payment: {str(e)}")

# Rota de teste/saúde
@app.route('/')
def health_check():
    return {
        "status": "online",
        "message": "API Share2Inspire em funcionamento",
        "version": "1.0.0"
    }

# Imprimir variáveis de ambiente disponíveis
logger.info("=== VARIÁVEIS DE AMBIENTE DISPONÍVEIS ===")
for key in ["BREVO_API_KEY", "IFTHENPAY_API_KEY", "IFTHENPAY_CALLBACK_SECRET", 
           "IFTHENPAY_MBWAY_KEY", "IFTHENPAY_PAYSHOP_KEY", "IFTHENPAY_MULTIBANCO_ENTITY", 
           "IFTHENPAY_MULTIBANCO_SUBENTITY", "FLASK_SECRET_KEY"]:
    logger.info(f"{key}: {'DEFINIDA' if os.getenv(key) else 'NÃO DEFINIDA'}")

# Se executado diretamente
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "False").lower() == "true")
