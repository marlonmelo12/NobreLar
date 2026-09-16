"""Testes de integração para cálculo de matriz de distâncias e Caixeiro Viajante (TSP)."""

import pytest
from app.services.distance_matrix import haversine_road_distance_km, build_distance_matrix
from app.services.tsp_solver import solve_tsp


def test_haversine_road_distance():
    """Valida distância viária entre o CD Crateús (-5.1784, -40.6775) e Ipaporanga (-4.9011, -40.7589)."""
    cd_crateus = (-5.1784, -40.6775)
    ipaporanga = (-4.9011, -40.7589)

    dist_km = haversine_road_distance_km(cd_crateus, ipaporanga)
    # Distância em linha reta ~32km * 1.28 ~ 41km
    assert 38.0 <= dist_km <= 45.0


def test_solve_tsp_and_lifo_order():
    """Valida roteirização ótima do TSP e sequenciamento inverso LIFO de carregamento na doca."""
    # Nó 0: CD Crateús
    # Nó 1: Ipaporanga
    # Nó 2: Poranga
    # Nó 3: Ararendá
    locations = [
        (-5.1784, -40.6775),  # 0: CD Crateús
        (-4.9011, -40.7589),  # 1: Ipaporanga
        (-4.7472, -40.9161),  # 2: Poranga
        (-4.7419, -40.8256),  # 3: Ararendá
    ]

    res = solve_tsp(locations, depot_index=0, roundtrip=True)

    assert res["status"] in ("OPTIMAL", "FEASIBLE")
    assert res["route"][0] == 0  # Inicia no CD Crateús
    assert res["route"][-1] == 0  # Retorna ao CD Crateús
    assert res["total_distance_km"] > 0.0

    # Validação do sequenciamento LIFO (o último cliente a receber é carregado primeiro no fundo)
    delivery_order = res["delivery_order"]
    lifo_order = res["lifo_loading_order"]

    assert len(delivery_order) == 3
    assert len(lifo_order) == 3
    assert lifo_order == list(reversed(delivery_order))
