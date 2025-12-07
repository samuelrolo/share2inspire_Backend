import os
import logging
from google.cloud import secretmanager

# Configurar logging
logger = logging.getLogger(__name__)

def get_secret(secret_id, default=None, project_id=None):
    """
    Obtém um segredo do Google Secret Manager ou variáveis de ambiente.
    
    A ordem de precedência é:
    1. Variável de ambiente (para desenvolvimento local/overrides)
    2. Google Secret Manager
    3. Valor default
    """
    # 1. Tentar variável de ambiente
    env_val = os.getenv(secret_id)
    if env_val:
        return env_val
        
    # 2. Tentar Secret Manager
    try:
        # Se project_id não for fornecido, tentar obter do ambiente
        if not project_id:
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
            
        if not project_id:
            logger.warning(f"GOOGLE_CLOUD_PROJECT não definido. Não é possível buscar '{secret_id}' no Secret Manager.")
            return default

        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        
        response = client.access_secret_version(request={"name": name})
        secret_val = response.payload.data.decode("UTF-8")
        
        return secret_val
        
    except Exception as e:
        logger.warning(f"Erro ao obter segredo '{secret_id}' do Secret Manager: {e}")
        return default
