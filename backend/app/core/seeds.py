"""Cargas iniciais (seeds) oficiais do sistema NobreLOG IA.

Contém a parametrização inicial da frota de veículos (com a separação do
Kia Bongo e Hyundai HR, e restrições territoriais), perfis de otimização,
eixos rodoviários, cidades e usuários do sistema com controle RBAC.
"""

from typing import List, Dict, Any
from app.core.constants import CITY_TO_AXIS_MAP
from app.core.geo_constants import REGION_COORDINATES_CACHE

# Frota Oficial Parametrizada da Nobre Lar: 2 Caminhões Grandes e 2 Caminhões Médios
DEFAULT_VEHICLES: List[Dict[str, Any]] = [
    {
        "id": "accelo-815-01",
        "name": "Mercedes-Benz Accelo 815 (Caminhão Grande 01)",
        "plate": "NBL-8151",
        "capacity_kg": 4800.0,
        "useful_volume_m3": 18.50,      # Cubagem útil operacional com estivagem (ADR-0010)
        "useful_length_m": 5.50,
        "allows_long_items": True,       # Comporta tubos e treliças de 6m
        "restricted_to_crateus": False,  # Intermunicipal: opera em todos os eixos rodoviários
        "operates_intermunicipal": True,
        "active": True,
    },
    {
        "id": "accelo-815-02",
        "name": "Mercedes-Benz Accelo 815 (Caminhão Grande 02)",
        "plate": "NBL-8152",
        "capacity_kg": 4800.0,
        "useful_volume_m3": 18.50,      # Cubagem útil operacional com estivagem (ADR-0010)
        "useful_length_m": 5.50,
        "allows_long_items": True,       # Comporta tubos e treliças de 6m
        "restricted_to_crateus": False,  # Intermunicipal: opera em todos os eixos rodoviários
        "operates_intermunicipal": True,
        "active": True,
    },
    {
        "id": "kia-bongo-01",
        "name": "Kia Bongo K2500 (Caminhão Médio 01)",
        "plate": "NBL-2500",
        "capacity_kg": 1700.0,
        "useful_volume_m3": 6.50,
        "useful_length_m": 3.10,
        "allows_long_items": False,      # Não comporta peças lineares de 6m
        "restricted_to_crateus": True,   # Restrito ao município de Crateús e seus distritos
        "operates_intermunicipal": False,
        "active": True,
    },
    {
        "id": "hyundai-hr-01",
        "name": "Hyundai HR (Caminhão Médio 02)",
        "plate": "NBL-2600",
        "capacity_kg": 1700.0,
        "useful_volume_m3": 6.50,
        "useful_length_m": 3.10,
        "allows_long_items": False,      # Não comporta peças lineares de 6m
        "restricted_to_crateus": True,   # Restrito ao município de Crateús e seus distritos
        "operates_intermunicipal": False,
        "active": True,
    },
]

# Perfis Oficiais de Otimização Multicritério (RF-009 e RF-009-B)
DEFAULT_PROFILES: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "Equilibrado",
        "w_peso": 0.25,
        "w_volume": 0.25,
        "w_valor": 0.30,
        "w_quantidade": 0.20,
        "objective_mode": "score_agregado",
        "is_default": True,
        "description": "Perfil padrão da operação diária, balanceando ocupação física e faturamento.",
    },
    {
        "id": 2,
        "name": "Comercial",
        "w_peso": 0.15,
        "w_volume": 0.15,
        "w_valor": 0.50,
        "w_quantidade": 0.20,
        "objective_mode": "score_agregado",
        "is_default": False,
        "description": "Prioriza pedidos de alto valor financeiro para fechamento de mês ou metas.",
    },
    {
        "id": 3,
        "name": "Capacidade",
        "w_peso": 0.35,
        "w_volume": 0.35,
        "w_valor": 0.20,
        "w_quantidade": 0.10,
        "objective_mode": "score_agregado",
        "is_default": False,
        "description": "Maximiza a ocupação física cúbica e ponderal para desovar estoque volumoso.",
    },
    {
        "id": 4,
        "name": "Eficiência",
        "w_peso": 0.25,
        "w_volume": 0.25,
        "w_valor": 0.30,
        "w_quantidade": 0.20,
        "objective_mode": "eficiencia",
        "is_default": False,
        "description": "Prioriza valor comercial entregue por unidade de capacidade consumida.",
    },
]

# Eixos Rodoviários Canônicos
DEFAULT_AXES: List[Dict[str, Any]] = [
    {"id": "eixo-0-crateus-urbano", "name": "Crateús Urbano", "active": True},
    {"id": "eixo-1-fronteira-pi", "name": "Fronteira Piauí", "active": True},
    {"id": "eixo-2-sertao-central", "name": "Sertão Central", "active": True},
    {"id": "eixo-3-sul", "name": "Eixo Sul", "active": True},
    {"id": "eixo-4-norte-serra", "name": "Norte e Serra", "active": True},
    {"id": "eixo-5-inhamuns", "name": "Inhamuns", "active": True},
]

# Usuários Padrão para o RBAC do MVP (RF-017)
DEFAULT_USERS: List[Dict[str, Any]] = [
    {"username": "operador", "password": "operador123", "role": "operador"},
    {"username": "aprovador", "password": "aprovador123", "role": "aprovador"},
    {"username": "admin", "password": "admin123", "role": "admin"},
]
