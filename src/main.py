"""
Este ficheiro é uma versão modificada do src/main.py fornecido pelo utilizador,
integrando o carregamento de segredos (chaves API) a partir do Google Cloud Secret Manager
e reestruturado para usar o padrão de Application Factory com create_app().

Certifique-se de que:
1. Os segredos (`BREVO_API_KEY`, `IFTHENPAY_GATEWAY_KEY`, `IFTHENPAY_CALLBACK_KEY`, 
   `IFTHENPAY_MBWAY_KEY`, `IFTHENPAY_PAYSHOP_KEY`, `FLASK_SECRET_KEY`) estão criados no Google Cloud Secret Manager
   com os nomes exatos aqui referidos como IDs dos segredos.
2. A conta de serviço do App Engine tem permissões para aceder a estes segredos (papel "Secret Manager Secret Accessor").
3. A biblioteca `google-cloud-secret-manager` está no seu `requirements.txt` e instalada.
"""
import os
import sys

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from dotenv import load_dotenv

# Tentar importar a biblioteca do Secret Manager
try:
    from google.cloud import secretmanager
    SECRET_MANAGER_AVAILABLE = True
except ImportError:
    SECRET_MANAGER_AVAILABLE = False
    print("AVISO: Biblioteca google-cloud-secret-manager não encontrada. Não será possível carregar segredos da GCP.")
    print("Execute 'pip install google-cloud-secret-manager' e adicione ao requirements.txt")

# Import Blueprints
# from src.models.user import db # Database not used yet
# from src.routes.user import user_bp # Default user blueprint not used yet
from src.routes.feedback import feedback_bp
from src.routes.payment import payment_bp # Assegure-se que este import está correto e o ficheiro existe

# Carregar variáveis de ambiente do ficheiro .env (para desenvolvimento local)
load_dotenv() # Idealmente chamado dentro de create_app ou antes, se as configs são lidas globalmente antes da app factory

# Função para aceder a segredos do Google Cloud Secret Manager
def get_secret(project_id, secret_id, version_id="latest"):
    if not SECRET_MANAGER_AVAILABLE:
        print(f"AVISO: Tentativa de aceder ao segredo {secret_id} mas Secret Manager não está disponível.")
        return None
    
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    try:
        response = client.access_secret_version(request={"name": name})
        secret_value = response.payload.data.decode("UTF-8")
        print(f"Segredo {secret_id} carregado com sucesso do Secret Manager.")
        return secret_value
    except Exception as e:
        print(f"ERRO ao aceder ao segredo {secret_id} no projeto {project_id}: {e}")
        print(f"Verifique se o segredo existe com o ID '{secret_id}', se a API Secret Manager está ativa e se a conta de serviço tem permissões.")
        return None

def create_app():
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

    # Carregar segredos da Google Cloud Secret Manager
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT") # App Engine define esta variável automaticamente

    SECRETS_TO_LOAD_FROM_GCP = [
        "BREVO_API_KEY",
        "IFTHENPAY_GATEWAY_KEY",
        "IFTHENPAY_CALLBACK_KEY",
        "IFTHENPAY_MBWAY_KEY",
        "IFTHENPAY_PAYSHOP_KEY",
        "FLASK_SECRET_KEY"
    ]

    if project_id and SECRET_MANAGER_AVAILABLE:
        print(f"A carregar segredos para o projeto GCP: {project_id}")
        for secret_name in SECRETS_TO_LOAD_FROM_GCP:
            secret_value = get_secret(project_id, secret_name)
            if secret_value:
                os.environ[secret_name] = secret_value # Disponibiliza como variável de ambiente
                if secret_name == 'FLASK_SECRET_KEY':
                    app.config['SECRET_KEY'] = secret_value # Configura diretamente na app
            else:
                if not os.getenv(secret_name):
                     print(f"AVISO CRÍTICO: {secret_name} não foi carregada do Secret Manager nem definida via .env. A aplicação pode falhar.")
    elif not project_id and SECRET_MANAGER_AVAILABLE:
        print("AVISO: GOOGLE_CLOUD_PROJECT não definido. Não foi possível carregar segredos do Secret Manager.")
        print("Se estiver em desenvolvimento local e quiser testar o Secret Manager, defina GOOGLE_CLOUD_PROJECT e autentique-se com 'gcloud auth application-default login'.")

    # Configurar FLASK_SECRET_KEY (garantir que está definida)
    # Prioridade: Secret Manager (já feito acima) -> .env -> (Não deve haver default inseguro em produção)
    if not app.config.get('SECRET_KEY'): # Se não foi carregada do Secret Manager
        app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY') # Tenta carregar do .env
    
    if not app.config.get('SECRET_KEY'):
        print("ALERTA DE SEGURANÇA CRÍTICO: FLASK_SECRET_KEY não está definida! Configure-a no Secret Manager ou via .env para desenvolvimento.")
        if os.getenv('FLASK_ENV', 'production').lower() != 'production':
            app.config['SECRET_KEY'] = 'temp_dev_secret_key_change_me_later'
            print("Usando FLASK_SECRET_KEY temporária e insegura para desenvolvimento. NÃO USE EM PRODUÇÃO.")
        # Em produção, a aplicação não deve iniciar sem uma FLASK_SECRET_KEY segura.
        # Considerar levantar uma exceção aqui se estiver em produção e a chave não estiver definida.

    # Registar os blueprints
    # app.register_blueprint(user_bp, url_prefix='/api') # Manter comentado se não for usado
    app.register_blueprint(feedback_bp)
    app.register_blueprint(payment_bp)

    # Configuração da Base de Dados (manter comentado por agora)
    # ... (código da base de dados como estava antes) ...

    # Rota para servir ficheiros estáticos (ex: frontend se integrado) ou index.html
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        static_folder_path = app.static_folder
        if static_folder_path is None:
                return "Pasta estática não configurada", 404

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return "index.html não encontrado na pasta estática.", 404
    
    return app

# O bloco if __name__ == '__main__': é para execução local, não é usado pelo Gunicorn no App Engine
if __name__ == '__main__':
    app = create_app() # Cria a app usando a factory para desenvolvimento local
    
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 8080))
    
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ['true', '1', 't'] 
    if os.getenv("GOOGLE_CLOUD_PROJECT"):
        debug_mode = False
        print("Ambiente GCP detetado. FLASK_DEBUG definido como False.")
    
    print(f"A iniciar servidor Flask em {host}:{port} (Debug: {debug_mode})")
    app.run(host=host, port=port, debug=debug_mode)

