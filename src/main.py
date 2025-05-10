"""
Este ficheiro é uma versão modificada do src/main.py fornecido pelo utilizador,
integrando o carregamento de segredos (chaves API) a partir do Google Cloud Secret Manager.

Certifique-se de que:
1. Os segredos (`BREVO_API_KEY`, `IFTHENPAY_GATEWAY_KEY`, `IFTHENPAY_CALLBACK_KEY`, 
   `IFTHENPAY_MBWAY_KEY`, `IFTHENPAY_PAYSHOP_KEY`, `FLASK_SECRET_KEY`) estão criados no Google Cloud Secret Manager
   com os nomes exatos aqui referidos como IDs dos segredos.
2. A conta de serviço do App Engine tem permissões para aceder a estes segredos.
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
    "FLASK_SECRET_KEY"
    # Adicione outras chaves de API ou credenciais aqui, como DB_PASSWORD, etc.
]

if project_id and SECRET_MANAGER_AVAILABLE:
    print(f"A carregar segredos para o projeto GCP: {project_id}")
    for secret_name in SECRETS_TO_LOAD_FROM_GCP:
        secret_value = get_secret(project_id, secret_name)
        if secret_value:
            os.environ[secret_name] = secret_value
        else:
            # Se o segredo não for carregado e não estiver já no ambiente (ex: via .env para dev local),
            # a aplicação poderá não funcionar corretamente. FLASK_SECRET_KEY é um caso especial.
            if secret_name == "FLASK_SECRET_KEY" and not os.getenv(secret_name):
                print(f"AVISO: {secret_name} não carregada do Secret Manager. Usar um valor por defeito é INSEGURO PARA PRODUÇÃO.")
                # os.environ[secret_name] = "fallback_default_secret_key_isso_nao_deve_acontecer_em_prod" # Removido para forçar configuração
            elif not os.getenv(secret_name):
                 print(f"AVISO CRÍTICO: {secret_name} não foi carregada do Secret Manager nem definida via .env. A aplicação pode falhar.")
elif not project_id and SECRET_MANAGER_AVAILABLE:
    print("AVISO: GOOGLE_CLOUD_PROJECT não definido. Não foi possível carregar segredos do Secret Manager.")
    print("Se estiver em desenvolvimento local e quiser testar o Secret Manager, defina GOOGLE_CLOUD_PROJECT e autentique-se com 'gcloud auth application-default login'.")

# Criação da Aplicação Flask
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configurar FLASK_SECRET_KEY
# Prioridade: Secret Manager -> .env -> (Não deve haver default inseguro em produção)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
if not app.config['SECRET_KEY']:
    print("ALERTA DE SEGURANÇA CRÍTICO: FLASK_SECRET_KEY não está definida! Configure-a no Secret Manager ou via .env para desenvolvimento.")
    # Em produção, a aplicação não deve iniciar sem uma FLASK_SECRET_KEY segura.
    # Para desenvolvimento, pode-se usar um valor temporário, mas NUNCA em produção:
    if os.getenv('FLASK_ENV', 'production').lower() != 'production': # ou FLASK_DEBUG == True
        app.config['SECRET_KEY'] = 'temp_dev_secret_key_change_me'
        print("Usando FLASK_SECRET_KEY temporária para desenvolvimento. NÃO USE EM PRODUÇÃO.")
    else:
        # Poderia levantar uma excepção aqui para impedir o arranque em produção sem a chave
        pass 

# Registar os blueprints
# app.register_blueprint(user_bp, url_prefix='/api') # Manter comentado se não for usado
app.register_blueprint(feedback_bp)
app.register_blueprint(payment_bp)

# Configuração da Base de Dados (manter comentado por agora)
# db_username = os.getenv('DB_USERNAME', 'root')
# db_password = os.getenv('DB_PASSWORD') # Carregar do Secret Manager em produção (ex: criar segredo DB_PASSWORD)
# db_host = os.getenv('DB_HOST', 'localhost')
# db_port = os.getenv('DB_PORT', '3306')
# db_name = os.getenv('DB_NAME', 'mydb')
# if db_password: # Só configurar se a password estiver disponível
#     app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#     # db.init_app(app) # Supondo que 'db' é o seu objeto SQLAlchemy
#     # with app.app_context():
#     #     db.create_all()
# else:
#     print("AVISO: DB_PASSWORD não definida. Configuração da base de dados ignorada.")

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

