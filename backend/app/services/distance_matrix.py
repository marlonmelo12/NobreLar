"""Módulo de cálculo de matriz de distâncias viárias e fórmula de Haversine.

Implementa os cálculos geométricos com fator de tortuosidade rodoviária (1.28)
para a malha do Sertão de Crateús e Inhamuns, conforme Seção 14 da v3.0 e docs/13.
"""

import math
from typing import List, Tuple
from app.core.constants import ROAD_TORTUOSITY_FACTOR


def haversine_road_distance_km(
    coord1: Tuple[float, float],
    coord2: Tuple[float, float],
    road_factor: float = ROAD_TORTUOSITY_FACTOR
) -> float:
    """Calcula a distância estimada por rodovia (em km) entre duas coordenadas geográficas.

    Utiliza a fórmula geodésica do grande círculo (Haversine) multiplicada pelo
    fator de tortuosidade rodoviária regional (1.28 para o interior cearense).
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    # Se as coordenadas forem idênticas, distância é zero
    if abs(lat1 - lat2) < 1e-6 and abs(lon1 - lon2) < 1e-6:
        return 0.0

    r_earth = 6371.0  # Raio médio da Terra em km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2.0) ** 2) + math.cos(phi1) * math.cos(phi2) * (math.sin(dlambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    geodesic_dist = r_earth * c

    return round(geodesic_dist * road_factor, 2)


def build_distance_matrix(locations: List[Tuple[float, float]]) -> List[List[int]]:
    """Gera uma matriz de distâncias K x K em metros inteiros para o OR-Tools Routing API.

    locations: Lista de tuplas (lat, lon), onde o índice 0 é o depósito (CD Crateús).
    """
    n = len(locations)
    matrix: List[List[int]] = [[0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i != j:
                dist_km = haversine_road_distance_km(locations[i], locations[j])
                matrix[i][j] = int(dist_km * 1000)  # Inteiro em metros

    return matrix
