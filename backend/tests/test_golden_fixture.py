"""Gabarito de Teste Unitário Oficial (Golden Test Fixture) do Guia de Implementação (doc 12).

Valida a alocação de carga do Eixo 4 (Norte e Serra: Ipaporanga/Poranga)
comparando o Mercedes Accelo 815 com o Kia Bongo K2500 diante de peças de 6 metros.
"""

import pytest
from app.services.optimizer_cpsat import solve_load_allocation
from app.services.validation import IndependentValidator


def test_golden_allocation_eixo4_accelo():
    """Valida que o Accelo 815 comporta itens de 6m e respeita a capacidade de 4.800 kg e 18,5 m³."""
    sample_orders = [
        {"id": "L01", "total_weight_kg": 2000.0, "total_volume_m3": 1.5, "total_value": 4500.0, "has_long_items": False, "axis_id": "eixo-4-norte-serra"},
        {"id": "L02", "total_weight_kg": 1800.0, "total_volume_m3": 1.2, "total_value": 3900.0, "has_long_items": False, "axis_id": "eixo-4-norte-serra"},
        {"id": "L03", "total_weight_kg": 900.0,  "total_volume_m3": 0.8, "total_value": 2100.0, "has_long_items": False, "axis_id": "eixo-4-norte-serra"},
        {"id": "L04", "total_weight_kg": 500.0,  "total_volume_m3": 0.4, "total_value": 1100.0, "has_long_items": False, "axis_id": "eixo-4-norte-serra"},
        {"id": "L05", "total_weight_kg": 150.0,  "total_volume_m3": 0.2, "total_value": 350.0,  "has_long_items": True,  "axis_id": "eixo-4-norte-serra"},
    ]

    # Teste 1: Accelo 815 (Comporta 6m, 4.800 kg, 18,50 m³)
    result = solve_load_allocation(
        orders=sample_orders,
        capacity_kg=4800.0,
        capacity_m3=18.50,
        allows_long_items=True
    )

    assert result["status"] in ("OPTIMAL", "FEASIBLE"), "O solver deve encontrar solução viável/ótima."
    assert result["total_weight_kg"] <= 4800.0, "O peso não pode violar 4.800 kg."
    assert result["total_volume_m3"] <= 18.50, "O volume não pode violar 18,5 m³."
    assert "L05" in result["selected_order_ids"], "L05 contém peças de 6m e deve ser aceito no caminhão Accelo 815."

    # Validação independente do plano do Accelo
    selected_orders = [o for o in sample_orders if o["id"] in result["selected_order_ids"]]
    is_valid, errors = IndependentValidator.validate_plan(
        selected_orders=selected_orders,
        capacity_kg=4800.0,
        capacity_m3=18.50,
        target_axis_id="eixo-4-norte-serra",
        allows_long_items=True
    )
    assert is_valid, f"Validação independente falhou: {errors}"


def test_golden_allocation_eixo4_bongo_rejects_6m():
    """Valida que o Kia Bongo K2500 rejeita expressamente pedidos com peças de 6 metros."""
    sample_orders = [
        {"id": "L01", "total_weight_kg": 2000.0, "total_volume_m3": 1.5, "total_value": 4500.0, "has_long_items": False},
        {"id": "L02", "total_weight_kg": 1800.0, "total_volume_m3": 1.2, "total_value": 3900.0, "has_long_items": False},
        {"id": "L03", "total_weight_kg": 900.0,  "total_volume_m3": 0.8, "total_value": 2100.0, "has_long_items": False},
        {"id": "L04", "total_weight_kg": 500.0,  "total_volume_m3": 0.4, "total_value": 1100.0, "has_long_items": False},
        {"id": "L05", "total_weight_kg": 150.0,  "total_volume_m3": 0.2, "total_value": 350.0,  "has_long_items": True},
    ]

    # Teste 2: Bongo K2500 (NÃO comporta 6m, 1.700 kg, 6,50 m³)
    result_bongo = solve_load_allocation(
        orders=sample_orders,
        capacity_kg=1700.0,
        capacity_m3=6.50,
        allows_long_items=False
    )

    assert result_bongo["status"] in ("OPTIMAL", "FEASIBLE")
    assert "L05" not in result_bongo["selected_order_ids"], "L05 NÃO pode ser alocado no Bongo (restrição de 6m)!"
    assert result_bongo["total_weight_kg"] <= 1700.0, "Peso total deve respeitar o limite de 1.700 kg do Bongo."
    assert result_bongo["total_volume_m3"] <= 6.50, "Volume total deve respeitar o limite de 6,5 m³ do Bongo."
