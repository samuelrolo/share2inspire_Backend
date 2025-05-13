import secrets
import base64

# Gerar uma chave secreta forte
secret_key = base64.b64encode(secrets.token_bytes(32)).decode('utf-8')

print(f"A sua Flask Secret Key gerada é: {secret_key}")
