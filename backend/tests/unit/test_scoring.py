"""Testes unitários para o módulo de cálculo de scores multicritério e eficiência."""

import pytest
from app.services.scoring import calculate_order_scores


def test_scoring_weights_sum_validation():
    """Valida que perfis cuja soma dos pesos != 1.0 geram ValueError."""
    mock_orders = [{"id": "L01", "total_weight_kg": 100.0, "total_volume_m3": 1.0, "total_value": 500.0}]
    with pytest.raises(ValueError, match="soma dos pesos"):
        calculate_order_scores(
            orders=mock_orders,
            capacity_kg=1000.0,
            capacity_m3=10.0,
            w_peso=0.5,
            w_volume=0.5,
            w_valor=0.5,
            w_quantidade=0.5  # soma = 2.0
        )


def test_scoring_logarithmic_normalization():
    """Valida normalização logarítmica e ausência de distorção por outliers."""
    mock_orders = [
        {"id": "L01", "total_weight_kg": 500.0, "total_volume_m3": 2.0, "total_value": 10000.0, "sale_frequency": 10},
        {"id": "L02", "total_weight_kg": 200.0, "total_volume_m3": 1.0, "total_value": 1000.0, "sale_frequency": 1},
        {"id": "L03", "total_weight_kg": 100.0, "total_volume_m3": 0.5, "total_value": 0.0, "sale_frequency": 0},
    ]

    scored = calculate_order_scores(
        orders=mock_orders,
        capacity_kg=1000.0,
        capacity_m3=10.0,
        w_peso=0.25,
        w_volume=0.25,
        w_valor=0.30,
        w_quantidade=0.20
    )

    assert len(scored) == 3
    # L01 deve possuir o maior score agregado e eficiência definida
    assert scored[0]["score"] > scored[1]["score"] > scored[2]["score"]
    assert 0.0 <= scored[0]["score"] <= 1.0
    assert 0.0 <= scored[1]["score"] <= 1.0
    assert 0.0 <= scored[2]["score"] <= 1.0
    assert scored[0]["efficiency"] > 0.0


def test_scoring_edge_case_zero_capacities():
    """Valida rejeição de capacidades nulas ou negativas."""
    mock_orders = [{"id": "L01", "total_weight_kg": 10.0, "total_volume_m3": 0.1, "total_value": 50.0}]
    with pytest.raises(ValueError, match="estritamente positivas"):
        calculate_order_scores(orders=mock_orders, capacity_kg=0.0, capacity_m3=10.0)
