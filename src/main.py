# /home/ubuntu/share2inspire_backend/src/main.py

import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from dotenv import load_dotenv

# Import Blueprints
# from src.models.user import db # Database not used yet
# from src.routes.user import user_bp # Default user blueprint not used yet
from src.routes.feedback import feedback_bp
from src.routes.payment import payment_bp

# Carregar variáveis de ambiente do ficheiro .env
load_dotenv()

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'a_default_secret_key_for_dev') # Usar variável de ambiente

# Registar os blueprints
# app.register_blueprint(user_bp, url_prefix='/api') # Manter comentado se não for usado
app.register_blueprint(feedback_bp) # url_prefix já definido no blueprint
app.register_blueprint(payment_bp)  # url_prefix já definido no blueprint

# Configuração da Base de Dados (manter comentado por agora)
# app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'mydb')}"
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db.init_app(app)
# with app.app_context():
#     db.create_all()

# Rota para servir ficheiros estáticos (ex: frontend se integrado) ou index.html
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Pasta estática não configurada", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        # Serve ficheiro específico se existir
        return send_from_directory(static_folder_path, path)
    else:
        # Serve index.html por defeito para rotas não encontradas (útil para SPAs)
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            # Se não houver index.html, pode retornar uma API de status ou 404
            # return jsonify({"status": "Backend a funcionar"}), 200
            return "index.html não encontrado", 404

if __name__ == '__main__':
    # Usar variáveis de ambiente para host e porta, com defaults
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() in ['true', '1', 't'] # Ativar debug por defeito em dev
    
    print(f"A iniciar servidor Flask em {host}:{port} (Debug: {debug_mode})")
    app.run(host=host, port=port, debug=debug_mode)

