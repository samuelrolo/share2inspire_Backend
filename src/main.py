"""
Este ficheiro é uma versão modificada do src/main.py fornecido pelo utilizador,
integrando o carregamento de segredos (chaves API) a partir do Google Cloud Secret Manager
com fallback para variáveis de ambiente definidas no app.yaml.

Modificações:
1. Adicionada função create_app() para compatibilidade com App Engine
2. Melhorado o fallback para variáveis de ambiente quando o Secret Manager não está acessível
3. Reduzidos os avisos críticos quando as variáveis estão definidas no ambiente
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
load_dotenv()

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
    """
    Função factory para criar e configurar a aplicação Flask.
    Esta função é necessária para o App Engine encontrar e inicializar a aplicação.
    """
    # Criação da Aplicação Flask
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Carregar segredos da Google Cloud Secret Manager
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT") # App Engine define esta variável automaticamente

    # Nomes dos segredos como devem estar no Secret Manager (IDs dos segredos)
    # e como serão acedidos no código (chaves do dicionário os.environ)
    SECRETS_TO_LOAD_FROM_GCP = [
        "BREVO_API_KEY",
        "IFTHENPAY_GATEWAY_KEY",
        "IFTHENPAY_CALLBACK_KEY",
        "IFTHENPAY_MBWAY_KEY",
        "IFTHENPAY_PAYSHOP_KEY",
        "IFTHENPAY_MB_KEY",
        "FLASK_SECRET_KEY",
        "ANTI_PHISHING_KEY"
        # Adicione outras chaves de API ou credenciais aqui, como DB_PASSWORD, etc.
    ]

    # Tentar carregar segredos do Secret Manager, mas não falhar se não conseguir
    # (usará as variáveis de ambiente definidas no app.yaml como fallback)
    if project_id and SECRET_MANAGER_AVAILABLE:
        print(f"A carregar segredos para o projeto GCP: {project_id}")
        for secret_name in SECRETS_TO_LOAD_FROM_GCP:
            # Só tenta carregar do Secret Manager se a variável não estiver já definida no ambiente
            if not os.getenv(secret_name):
                secret_value = get_secret(project_id, secret_name)
                if secret_value:
                    os.environ[secret_name] = secret_value
                    print(f"Segredo {secret_name} carregado do Secret Manager.")
                else:
                    # Verificar se a variável está definida no ambiente (app.yaml)
                    if os.getenv(secret_name):
                        print(f"Usando {secret_name} definida no ambiente (app.yaml).")
                    else:
                        print(f"AVISO: {secret_name} não está disponível no Secret Manager nem no ambiente.")
            else:
                print(f"Usando {secret_name} já definida no ambiente (app.yaml).")
    elif not project_id and SECRET_MANAGER_AVAILABLE:
        print("AVISO: GOOGLE_CLOUD_PROJECT não definido. Não foi possível carregar segredos do Secret Manager.")
        print("Usando variáveis de ambiente definidas no app.yaml ou .env.")
    else:
        print("Secret Manager não disponível. Usando variáveis de ambiente definidas no app.yaml ou .env.")

    # Verificar variáveis críticas
    for var_name in SECRETS_TO_LOAD_FROM_GCP:
        if not os.getenv(var_name):
            if var_name == "FLASK_SECRET_KEY":
                print(f"ALERTA DE SEGURANÇA: {var_name} não está definida! Usando valor temporário (INSEGURO PARA PRODUÇÃO).")
                os.environ[var_name] = "temp_secret_key_insecure_for_production_only"
            else:
                print(f"AVISO: {var_name} não está definida. Algumas funcionalidades podem não funcionar corretamente.")

    # Configurar FLASK_SECRET_KEY
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
    if not app.config['SECRET_KEY']:
        print("ALERTA DE SEGURANÇA: FLASK_SECRET_KEY não está definida! Usando valor temporário (INSEGURO PARA PRODUÇÃO).")
        app.config['SECRET_KEY'] = 'temp_secret_key_insecure_for_production_only'

    # Registar os blueprints
    # app.register_blueprint(user_bp, url_prefix='/api') # Manter comentado se não for usado
    app.register_blueprint(feedback_bp)
    app.register_blueprint(payment_bp)

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
                return "index.html não encontrado na pasta estática.", 404

    return app

# Criar a aplicação usando a função factory
app = create_app()

if __name__ == '__main__':
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 8080)) # Porta 8080 é comum para App Engine
    
    # FLASK_DEBUG deve ser False em produção. Carregar do .env ou definir para False.
    # A variável de ambiente FLASK_ENV=(development|production) também é comum.
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ['true', '1', 't'] 
    if os.getenv("GOOGLE_CLOUD_PROJECT"):
        debug_mode = False # Forçar debug False em ambiente GCP (App Engine, Cloud Run, etc.)
        print("Ambiente GCP detetado. FLASK_DEBUG definido como False.")
    
    print(f"A iniciar servidor Flask em {host}:{port} (Debug: {debug_mode})")
    app.run(host=host, port=port, debug=debug_mode)
