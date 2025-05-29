import sys
import os

# Adiciona o diretório 'src' ao sys.path para permitir importações relativas
# como se estivéssemos a executar a partir do diretório pai de 'src'
# Isto pode não ser estritamente necessário se o seu PYTHONPATH estiver configurado
# ou se executar a partir do diretório correto, mas é uma boa prática para scripts de teste.
current_dir = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.dirname(current_dir) # Se test_app_import.py estiver em src
project_root = current_dir # Se test_app_import.py estiver na raiz do projeto
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

print(f"Tentando importar 'create_app' de src.main...")
print(f"sys.path inclui: {src_path}")

try:
    from main import create_app
    print("SUCESSO: A função create_app foi encontrada e importada de src.main!")
    app = create_app()
    print(f"Instância da aplicação criada com sucesso: {app}")
    print("Configuração da aplicação:")
    for key, value in app.config.items():
        print(f"  {key}: {value}")
    print("Blueprints registados:")
    for bp_name, bp in app.blueprints.items():
        print(f"  {bp_name}: {bp}")

except ImportError as e:
    print(f"ERRO DE IMPORTAÇÃO: {e}")
    print("Verifique se o ficheiro src/main.py existe e se o nome da função create_app está correto.")
    print("Verifique também se está a executar este script a partir da pasta raiz do projeto.")
except AttributeError as e:
    print(f"ERRO DE ATRIBUTO: {e}")
    print("A função create_app pode não estar definida em src/main.py ou pode ter um nome diferente.")
except Exception as e:
    print(f"OCORREU UM ERRO INESPERADO: {e}")

