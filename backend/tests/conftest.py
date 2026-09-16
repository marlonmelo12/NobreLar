"""Configuração global do Pytest para o sistema NobreLOG IA."""

import sys
from pathlib import Path

# Adiciona o diretório backend ao sys.path para importação de app.*
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
