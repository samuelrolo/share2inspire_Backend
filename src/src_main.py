# src/main.py
import os
import logging
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Importar blueprints - CORRIGIDO: fedback em vez de feedback
from routes.fedback import feedback_bp
from routes.payment import payment_bp

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

def create_app():
    """
    Função factory para criar a aplicação Flask.
    Esta função é chamada pelo App Engine para inicializar a aplicação.
    """
    app = Flask(__name__)
    
    # Configurar CORS para permitir requisições de qualquer origem
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Configurar chave secreta
    app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24).hex())
    
    # Registar blueprints
    app.register_blueprint(feedback_bp)
    app.register_blueprint(payment_bp)
    
    # Rota de teste/saúde
    @app.route('/')
    def health_check():
        return {
            "status": "online",
            "message": "API Share2Inspire em funcionamento",
            "version": "1.0.0"
        }
    
    # Log de inicialização
    logger.info("Aplicação Flask inicializada com sucesso")
    logger.info("FLASK_SECRET_KEY: %s", "DEFINIDA" if app.secret_key else "NÃO DEFINIDA")
    
    return app

# Criar instância da aplicação para uso direto
# Isto permite que o objeto 'app' seja importado diretamente
app = create_app()

# Se executado diretamente
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "False").lower() == "true")
