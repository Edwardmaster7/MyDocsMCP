import os
import sys
from pathlib import Path

# Resolvemos o diretório raiz absoluto do projeto, assumindo que config.py está em src/
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DATA_DIR = PROJECT_ROOT / "data"

# Auto-cria a pasta data se não existir
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Define caminhos baseados na raiz do projeto (ou via variável de ambiente, se o usuário forçar)
PDF_DIR = os.environ.get("PDF_DIR", str(DATA_DIR / "pdfs"))
CHROMA_DIR = os.environ.get("CHROMA_DIR", str(DATA_DIR / "chroma_db"))
METADATA_DIR = os.environ.get("METADATA_DIR", str(DATA_DIR / "metadata"))

def log_stderr(*args, **kwargs):
    """
    Função utilitária para registrar logs no stderr em vez de stdout.
    Essencial para não quebrar a comunicação stdin/stdout padrão do protocolo MCP.
    """
    kwargs["flush"] = kwargs.get("flush", True)
    print(*args, file=sys.stderr, **kwargs)
