"""Módulo de parsers e sanitizadores de dados textuais e numéricos.

Contém expressões regulares e funções determinísticas para tratamento de:
- Moeda brasileira (R$ 1.250,50 -> 1250.50)
- Identificadores de pedido (12.608570 -> L12608570)
- Datas com erros de digitação históricos da base
- Extração de itens agregados (Itens_Resumo com código, descrição, quantidade e unidade)
- Normalização de endereços completos
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional

# Expressão regular canônica para desmembrar itens do resumo
ITEM_REGEX = re.compile(
    r'^\s*(?P<code>\d+)\s*-\s*(?P<desc>.*?)\s*\((?P<qtd>[\d.,]+)\s*(?P<unit>[A-Za-z0-9]+)\)\s*$'
)


def clean_currency(val: Any) -> float:
    """Converte strings de moeda brasileira (R$ 1.234,56), floats ou inteiros para float."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s_val = str(val).strip()
    if not s_val or s_val.lower() == "nan" or s_val == "":
        return 0.0
    s = s_val.replace("R$", "").replace(" ", "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def sanitize_order_id(raw_id: Any) -> str:
    """Sanitiza o código do pedido para o padrão canônico L{dígitos}.

    Exemplos:
    - '12.608570' -> 'L12608570'
    - 'L12609716.' -> 'L12609716'
    - '8507035' -> 'L8507035'
    """
    if raw_id is None:
        return "INVALIDO"
    digits = re.sub(r"[^0-9]", "", str(raw_id))
    return f"L{digits}" if digits else "INVALIDO"


def sanitize_brazilian_date(d_str: Any) -> str:
    """Sanitiza datas brasileiras no formato dd/mm/aa ou dd/mm/aaaa para ISO 8601 (YYYY-MM-DD).

    Aplica correções aos erros tipográficos históricos identificados na base de dados:
    - '26/08/14' -> '26/08/26'
    - '15/0826' -> '15/08/26'
    - '20/0826' -> '20/08/26'
    - '28/0/26' -> '28/08/26'
    - '290826' -> '29/08/26'
    """
    if d_str is None or str(d_str).strip().lower() == "nan" or not str(d_str).strip():
        return datetime.today().strftime("%Y-%m-%d")

    s = str(d_str).strip()

    # Correções específicas de inconsistências da base original
    s = s.replace("26/08/14", "26/08/26")
    s = s.replace("15/0826", "15/08/26").replace("20/0826", "20/08/26")
    s = s.replace("28/0/26", "28/08/26").replace("290826", "29/08/26")

    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    return datetime.today().strftime("%Y-%m-%d")


def parse_order_items(raw_items_str: str) -> List[Dict[str, Any]]:
    """Desmembra a string concatenada de itens (separados por '|') em dicionários estruturados.

    Exemplo de entrada:
    '12185 - CX. DAGUA BAKOF 1000L C/TMP (1,00 UN) | 21503 - CIMENTO POTY 50KG (80,00 UN)'
    """
    if not raw_items_str or str(raw_items_str).lower() == "nan":
        return []

    items = []
    tokens = str(raw_items_str).split("|")
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        match = ITEM_REGEX.match(token)
        if match:
            code = match.group("code").strip()
            desc = match.group("desc").strip()
            qtd_str = match.group("qtd").replace(".", "").replace(",", ".")
            unit = match.group("unit").strip().upper()
            try:
                qtd = float(qtd_str)
            except ValueError:
                qtd = 1.0

            items.append({
                "product_code": code,
                "product_desc": desc,
                "quantity": qtd,
                "unit": unit
            })
        else:
            # Fallback para itens com pontuação incomum
            items.append({
                "product_code": "00000",
                "product_desc": token,
                "quantity": 1.0,
                "unit": "UN"
            })

    return items


def parse_address_components(address_raw: Optional[str]) -> Dict[str, Optional[str]]:
    """Extrai componentes estruturados de endereço a partir de uma string textual livre.

    Suporta logradouro, número, bairro e CEP caso informados.
    """
    if not address_raw or str(address_raw).strip().lower() == "nan":
        return {
            "address_line": None,
            "address_number": None,
            "complement": None,
            "neighborhood": None,
            "postal_code": None,
        }

    raw = str(address_raw).strip()

    # Busca por CEP (ex: 63700-000 ou 63700000)
    cep_match = re.search(r"\b(\d{5}-?\d{3})\b", raw)
    cep = cep_match.group(1) if cep_match else None

    # Busca por número (ex: nº 120, N 1234, , 45)
    num_match = re.search(r"(?:[Nn]º?|[Nn]umero|[Nn]úmero)?\s*[, -]?\s*(\d+[A-Za-z]?)\b", raw)
    number = num_match.group(1) if num_match else None

    # Bairro (ex: Bairro Centro, B. Planalto)
    bairro_match = re.search(r"(?:[Bb]airro|[Bb]\.)\s*([^,-]+)", raw)
    bairro = bairro_match.group(1).strip() if bairro_match else None

    return {
        "address_line": raw,
        "address_number": number,
        "complement": None,
        "neighborhood": bairro,
        "postal_code": cep,
    }
