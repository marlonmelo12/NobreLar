"""Testes unitários para o pré-processador de fatiamento (Order Splitting) e regras de limpeza."""

import pytest
from app.services.pre_processor import split_overweight_orders, validate_vehicle_territorial_compatibility
from app.services.cleaning import CleaningService


def test_order_splitting_overweight_order():
    """Valida que pedido maior que a capacidade (ex: 5.387 kg de cimento) é fatiado em subpedidos vinculados."""
    orders = [
        {
            "id": "L12609291",
            "total_weight_kg": 5387.80,
            "total_volume_m3": 3.88,
            "total_value": 6328.17,
            "has_long_items": False
        },
        {
            "id": "L12608500",
            "total_weight_kg": 1500.0,
            "total_volume_m3": 1.20,
            "total_value": 2000.0,
            "has_long_items": False
        }
    ]

    processed = split_overweight_orders(orders, max_capacity_kg=4800.0)

    # 1 pedido fatiado em 2 + 1 pedido mantido = 3 pedidos no total
    assert len(processed) == 3

    p1 = processed[0]
    p2 = processed[1]
    norm = processed[2]

    assert p1["id"] == "L12609291-P1"
    assert p1["is_split"] is True
    assert p1["parent_order_id"] == "L12609291"
    assert p1["total_weight_kg"] <= 4800.0

    assert p2["id"] == "L12609291-P2"
    assert p2["is_split"] is True
    assert p2["parent_order_id"] == "L12609291"

    # Preservação integral do peso e valor original
    assert round(p1["total_weight_kg"] + p2["total_weight_kg"], 2) == 5387.80
    assert round(p1["total_value"] + p2["total_value"], 2) == 6328.17

    assert norm["id"] == "L12608500"
    assert norm.get("is_split") is not True


def test_vehicle_territorial_validation():
    """Valida restrição operacional de Bongo/HR a Crateús e exigência de Accelo para outras cidades."""
    accelo = {"id": "accelo-815-01", "name": "Mercedes Accelo", "restricted_to_crateus": False}
    bongo = {"id": "kia-bongo-01", "name": "Kia Bongo", "restricted_to_crateus": True}
    hr = {"id": "hyundai-hr-01", "name": "Hyundai HR", "restricted_to_crateus": True}

    # 1. Accelo atende qualquer cidade (intermunicipal)
    ok, _ = validate_vehicle_territorial_compatibility(accelo, ["IPAPORANGA", "PORANGA"])
    assert ok is True

    # 2. Bongo e HR atendem Crateús e seus distritos
    ok, _ = validate_vehicle_territorial_compatibility(bongo, ["CRATEUS", "REALEJO", "TUCUNS"])
    assert ok is True
    ok, _ = validate_vehicle_territorial_compatibility(hr, ["CRATEUS", "IBIAPABA"])
    assert ok is True

    # 3. Bongo e HR são REJEITADOS para viagens a outras cidades
    ok, msg = validate_vehicle_territorial_compatibility(bongo, ["IPAPORANGA"])
    assert ok is False
    assert "restrito a Crateús" in msg

    ok, msg = validate_vehicle_territorial_compatibility(hr, ["NOVA RUSSAS"])
    assert ok is False
    assert "restrito a Crateús" in msg


def test_cleaning_service_discard_rules():
    """Valida as regras canônicas de descarte e geração de CleaningLog."""
    # Balcão (suporte legado CSV e novo campo situacao)
    ok, logs = CleaningService.evaluate_order({"Pedido": "L01", "Situacao_CSV_Entrega": "RETIRADA"})
    assert ok is False
    assert logs[0].rule_applied == "retirada_balcao"

    ok_b, logs_b = CleaningService.evaluate_order({"Pedido": "L01_B", "situacao": "RETIRADA"})
    assert ok_b is False
    assert logs_b[0].rule_applied == "retirada_balcao"

    # Cancelado (suporte legado CSV e novo campo situacao)
    ok, logs = CleaningService.evaluate_order({"Pedido": "L02", "Logistica": "CANCELADO"})
    assert ok is False
    assert logs[0].rule_applied == "pedido_cancelado"

    ok_c, logs_c = CleaningService.evaluate_order({"Pedido": "L02_B", "situacao": "CANCELADO"})
    assert ok_c is False
    assert logs_c[0].rule_applied == "pedido_cancelado"

    # Entrega urbana em Crateús no fluxo regional
    ok, logs = CleaningService.evaluate_order({"Pedido": "L03", "Cidade": "CRATEUS"}, scope_regional=True)
    assert ok is False
    assert logs[0].rule_applied == "entrega_local_crateus"

    # Pedido válido externo
    ok, logs = CleaningService.evaluate_order({"Pedido": "L04", "Cidade": "IPAPORANGA", "Logistica": "ENTREGUE"}, scope_regional=True)
    assert ok is True
    assert len(logs) == 0
