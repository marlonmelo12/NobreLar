"""Constantes operacionais e mapeamento canônico do sistema NobreLOG IA.

Define os eixos rodoviários, cidades, distritos e regras geográficas
estabelecidas para a macrorregião do Centro de Distribuição em Crateús - CE.
"""

from typing import Dict, Any

# Mapeamento Canônico: Localidade (Cidade/Distrito) -> Eixo Rodoviário e Ordem de Descarga
CITY_TO_AXIS_MAP: Dict[str, Dict[str, Any]] = {
    # Polo Principal e Centro de Distribuição
    "CRATEUS": {
        "axis_id": "eixo-0-crateus-urbano",
        "axis_name": "Crateús Urbano",
        "delivery_order": 0,
        "is_district": False,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    # Eixo 1: Fronteira Piauí
    "BURITI DOS MONTES": {
        "axis_id": "eixo-1-fronteira-pi",
        "axis_name": "Fronteira Piauí",
        "delivery_order": 1,
        "is_district": False,
        "parent_municipality": "BURITI DOS MONTES",
        "is_external": True,
    },
    "BARRO VERMELHO": {
        "axis_id": "eixo-1-fronteira-pi",
        "axis_name": "Fronteira Piauí",
        "delivery_order": 2,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    "TUCUNS": {
        "axis_id": "eixo-1-fronteira-pi",
        "axis_name": "Fronteira Piauí",
        "delivery_order": 3,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    "QUEIMADAS": {
        "axis_id": "eixo-1-fronteira-pi",
        "axis_name": "Fronteira Piauí",
        "delivery_order": 4,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    "FILOMENA": {
        "axis_id": "eixo-1-fronteira-pi",
        "axis_name": "Fronteira Piauí",
        "delivery_order": 5,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    # Eixo 2: Sertão Central
    "SUCESSO": {
        "axis_id": "eixo-2-sertao-central",
        "axis_name": "Sertão Central",
        "delivery_order": 1,
        "is_district": True,
        "parent_municipality": "TAMBORIL",
        "is_external": True,
    },
    "TAMBORIL": {
        "axis_id": "eixo-2-sertao-central",
        "axis_name": "Sertão Central",
        "delivery_order": 2,
        "is_district": False,
        "parent_municipality": "TAMBORIL",
        "is_external": True,
    },
    "NOVA RUSSAS": {
        "axis_id": "eixo-2-sertao-central",
        "axis_name": "Sertão Central",
        "delivery_order": 3,
        "is_district": False,
        "parent_municipality": "NOVA RUSSAS",
        "is_external": True,
    },
    "FAZENDA": {
        "axis_id": "eixo-2-sertao-central",
        "axis_name": "Sertão Central",
        "delivery_order": 4,
        "is_district": True,
        "parent_municipality": "NOVA RUSSAS",
        "is_external": True,
    },
    "IBIAPABA": {
        "axis_id": "eixo-2-sertao-central",
        "axis_name": "Sertão Central",
        "delivery_order": 5,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    # Eixo 3: Eixo Sul
    "INDEPENDENCIA": {
        "axis_id": "eixo-3-sul",
        "axis_name": "Eixo Sul",
        "delivery_order": 1,
        "is_district": False,
        "parent_municipality": "INDEPENDENCIA",
        "is_external": True,
    },
    "SAO JOSE": {
        "axis_id": "eixo-3-sul",
        "axis_name": "Eixo Sul",
        "delivery_order": 2,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    "ADAO": {
        "axis_id": "eixo-3-sul",
        "axis_name": "Eixo Sul",
        "delivery_order": 3,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    "VILA GRACA": {
        "axis_id": "eixo-3-sul",
        "axis_name": "Eixo Sul",
        "delivery_order": 4,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    "JATOBA DOS UMBELINOS": {
        "axis_id": "eixo-3-sul",
        "axis_name": "Eixo Sul",
        "delivery_order": 5,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    "SAO GONCALO": {
        "axis_id": "eixo-3-sul",
        "axis_name": "Eixo Sul",
        "delivery_order": 6,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    # Eixo 4: Norte e Serra
    "IPAPORANGA": {
        "axis_id": "eixo-4-norte-serra",
        "axis_name": "Norte e Serra",
        "delivery_order": 1,
        "is_district": False,
        "parent_municipality": "IPAPORANGA",
        "is_external": True,
    },
    "PORANGA": {
        "axis_id": "eixo-4-norte-serra",
        "axis_name": "Norte e Serra",
        "delivery_order": 2,
        "is_district": False,
        "parent_municipality": "PORANGA",
        "is_external": True,
    },
    "ARARENDA": {
        "axis_id": "eixo-4-norte-serra",
        "axis_name": "Norte e Serra",
        "delivery_order": 3,
        "is_district": False,
        "parent_municipality": "ARARENDA",
        "is_external": True,
    },
    "VACA MORTA": {
        "axis_id": "eixo-4-norte-serra",
        "axis_name": "Norte e Serra",
        "delivery_order": 4,
        "is_district": True,
        "parent_municipality": "PORANGA",
        "is_external": True,
    },
    "CURRAL VELHO": {
        "axis_id": "eixo-4-norte-serra",
        "axis_name": "Norte e Serra",
        "delivery_order": 5,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    "CURRAL DO MEIO": {
        "axis_id": "eixo-4-norte-serra",
        "axis_name": "Norte e Serra",
        "delivery_order": 6,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    "ROSARIO": {
        "axis_id": "eixo-4-norte-serra",
        "axis_name": "Norte e Serra",
        "delivery_order": 7,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    "PAU DE OLEIO": {
        "axis_id": "eixo-4-norte-serra",
        "axis_name": "Norte e Serra",
        "delivery_order": 8,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    # Eixo 5: Inhamuns
    "NOVO ORIENTE": {
        "axis_id": "eixo-5-inhamuns",
        "axis_name": "Inhamuns",
        "delivery_order": 1,
        "is_district": False,
        "parent_municipality": "NOVO ORIENTE",
        "is_external": True,
    },
    "REALEJO": {
        "axis_id": "eixo-5-inhamuns",
        "axis_name": "Inhamuns",
        "delivery_order": 2,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    "SANTANA": {
        "axis_id": "eixo-5-inhamuns",
        "axis_name": "Inhamuns",
        "delivery_order": 3,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    "MONTE NEBO": {
        "axis_id": "eixo-5-inhamuns",
        "axis_name": "Inhamuns",
        "delivery_order": 4,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    "SANTO ANDRE": {
        "axis_id": "eixo-5-inhamuns",
        "axis_name": "Inhamuns",
        "delivery_order": 5,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    "QUITERIANOPOLIS": {
        "axis_id": "eixo-5-inhamuns",
        "axis_name": "Inhamuns",
        "delivery_order": 6,
        "is_district": False,
        "parent_municipality": "QUITERIANOPOLIS",
        "is_external": True,
    },
    "BARRA DOS SIMIOES": {
        "axis_id": "eixo-5-inhamuns",
        "axis_name": "Inhamuns",
        "delivery_order": 7,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    "LAGOA DAS PEDRAS": {
        "axis_id": "eixo-5-inhamuns",
        "axis_name": "Inhamuns",
        "delivery_order": 8,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    "UMBURANA": {
        "axis_id": "eixo-5-inhamuns",
        "axis_name": "Inhamuns",
        "delivery_order": 9,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
    "SITIO GIRA SOL": {
        "axis_id": "eixo-5-inhamuns",
        "axis_name": "Inhamuns",
        "delivery_order": 10,
        "is_district": True,
        "parent_municipality": "CRATEUS",
        "is_external": False,
    },
}

# Fator de Escalonamento Aritmético para o OR-Tools CP-SAT (Aritmética Inteira)
SCALE_WEIGHT = 1_000        # kg para g (1g de precisão)
SCALE_VOLUME = 1_000_000    # m³ para cm³ (1cm³ de precisão)
SCALE_SCORE = 10_000        # Precisão de 4 casas decimais

# Constantes de Fatiamento de Cargas (Order Splitting)
SPLIT_TARGET_RATIO = 0.85   # Subpedido 1 recebe 85% da capacidade útil do veículo

# Fator de Tortuosidade Rodoviária (Distância Geodésica -> Rodovia no Sertão dos Inhamuns)
ROAD_TORTUOSITY_FACTOR = 1.28
