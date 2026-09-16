"""Coordenadas geográficas oficiais e cache regional offline do NobreLOG IA.

Contém as coordenadas oficiais do Centro de Distribuição em Crateús
e o dicionário de coordenadas das 24 localidades da macrorregião
para garantir operação com 100% de disponibilidade offline.
"""

from typing import Dict, Tuple, Any

# Coordenadas do Centro de Distribuição (Depósito Matriz da Nobre Lar)
DEPOT_COORDINATES: Dict[str, Any] = {
    "name": "CD Nobre Lar Crateús (Matriz)",
    "address": "Avenida Doutor Edilberto Frota, 2000, Planalto, Crateús - CE",
    "city": "CRATEUS",
    "state": "CE",
    "lat": -5.1784,
    "lon": -40.6775,
}

# Cache Estático Oficial de Coordenadas (Latitude, Longitude) das 24 Localidades
REGION_COORDINATES_CACHE: Dict[str, Tuple[float, float]] = {
    # Polo Principal e Depósito
    "CRATEUS": (-5.1784, -40.6775),
    # Eixo 1: Fronteira Piauí
    "BURITI DOS MONTES": (-5.3117, -41.0967),
    "BARRO VERMELHO": (-5.2530, -40.9850),
    "TUCUNS": (-5.2100, -40.8900),
    "QUEIMADAS": (-5.2800, -41.0200),
    "FILOMENA": (-5.3400, -41.1200),
    # Eixo 2: Sertão Central
    "SUCESSO": (-4.9542, -40.4283),
    "TAMBORIL": (-4.9317, -40.3236),
    "NOVA RUSSAS": (-4.7061, -40.5636),
    "FAZENDA": (-4.8500, -40.3800),
    "IBIAPABA": (-5.0333, -40.9167),
    # Eixo 3: Eixo Sul
    "INDEPENDENCIA": (-5.3961, -40.3094),
    "SAO JOSE": (-5.4200, -40.3500),
    "ADAO": (-5.4500, -40.4000),
    "VILA GRACA": (-5.3600, -40.2800),
    "JATOBA DOS UMBELINOS": (-5.4800, -40.4500),
    "SAO GONCALO": (-5.3000, -40.3200),
    # Eixo 4: Norte e Serra
    "IPAPORANGA": (-4.9011, -40.7589),
    "PORANGA": (-4.7472, -40.9161),
    "ARARENDA": (-4.7419, -40.8256),
    "VACA MORTA": (-4.8200, -40.8500),
    "CURRAL VELHO": (-4.8600, -40.8800),
    "CURRAL DO MEIO": (-4.8800, -40.8900),
    "ROSARIO": (-4.7800, -40.9400),
    "PAU DE OLEIO": (-4.8500, -40.7900),
    # Eixo 5: Inhamuns
    "NOVO ORIENTE": (-5.5347, -40.7742),
    "REALEJO": (-5.3500, -40.8167),
    "SANTANA": (-5.5800, -40.7200),
    "MONTE NEBO": (-5.1472, -40.8389),
    "SANTO ANDRE": (-5.6200, -40.7500),
    "QUITERIANOPOLIS": (-5.8119, -40.7028),
    "BARRA DOS SIMIOES": (-5.6700, -40.7100),
    "LAGOA DAS PEDRAS": (-5.4100, -40.7400),
    "UMBURANA": (-5.4600, -40.7600),
    "SITIO GIRA SOL": (-5.5100, -40.7800),
}
