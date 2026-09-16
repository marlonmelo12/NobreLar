"""Testes de integração para a API desacoplada, carroceria aberta e drill-down de itens.

Valida os contratos JSON estruturados baseados no modelo de pedido da Nobre Lar (N. L12608361).
"""

import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_mock_orders_json():
    """Valida o endpoint GET /api/v1/dispatch/mock-orders contendo a estrutura real do pedido."""
    res = client.get("/api/v1/dispatch/mock-orders")
    assert res.status_code == 200
    orders = res.json()
    assert isinstance(orders, list)
    assert len(orders) >= 5

    # Localiza o pedido exato da imagem oficial (L12608361)
    ped_oficial = next((p for p in orders if p["id"] == "L12608361"), None)
    assert ped_oficial is not None, "Pedido oficial L12608361 deve estar presente no mock"
    assert ped_oficial["cidade"] == "CRATEUS"
    assert ped_oficial["valor"] == 810.00
    assert len(ped_oficial["itens"]) == 3
    assert ped_oficial["itens"][0]["codigo"] == "23717"
    assert ped_oficial["itens"][0]["unidade"] == "MT"


def test_process_orders_decoupled_full():
    """Valida o endpoint POST /api/v1/dispatch/process-orders com drill-down e carroceria aberta."""
    res_mock = client.get("/api/v1/dispatch/mock-orders")
    orders_payload = res_mock.json()

    res = client.post(
        "/api/v1/dispatch/process-orders",
        json={"pedidos": orders_payload, "perfil_otimizacao": "Equilibrado"}
    )
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "SUCESSO"
    assert "resumo" in data
    assert "cargas_caminhao" in data
    assert "roteiros_entrega" in data
    assert "descartes_limpeza" in data

    # 1. Validação de Descartes de Limpeza (Balcão e Cancelado)
    descartes = data["descartes_limpeza"]
    pedidos_descartados = [d["pedido"] for d in descartes]
    assert "L12608998" in pedidos_descartados, "Pedido com RETIRADA balcão deve ser descartado"
    assert "L12608999" in pedidos_descartados, "Pedido Cancelado deve ser descartado"

    # 2. Validação da Visão Cargas no Caminhão (Carroceria Aberta + Drill-down)
    cargas = data["cargas_caminhao"]
    assert len(cargas) > 0
    for carga in cargas:
        assert "veiculo" in carga
        assert carga["veiculo"]["tipo_carroceria"] == "Carroceria Aberta (Grade Baixa)"
        assert "alerta_carroceria" in carga
        assert len(carga["pedidos_carroceria"]) > 0

        # Verifica a ordem e o drill-down dos itens
        for ped in carga["pedidos_carroceria"]:
            assert "ordem_carregamento" in ped
            assert "posicao_carroceria" in ped
            assert "itens" in ped
            assert len(ped["itens"]) > 0, "Cada pedido deve conter seu drill-down de itens"
            primeiro_item = ped["itens"][0]
            assert "codigo" in primeiro_item
            assert "descricao" in primeiro_item
            assert "peso_total_kg" in primeiro_item
            assert "volume_total_m3" in primeiro_item

    # 3. Validação da Visão Roteiros de Entrega (TSP + Endereços + Drill-down)
    roteiros = data["roteiros_entrega"]
    assert len(roteiros) > 0
    for rot in roteiros:
        assert len(rot["paradas"]) > 0
        for parada in rot["paradas"]:
            assert "parada" in parada
            assert "endereco_completo" in parada
            assert "status_pagamento" in parada
            assert "itens" in parada
            assert len(parada["itens"]) > 0, "Cada parada deve conter os itens a descarregar"


def test_process_orders_truck_load_endpoint():
    """Valida o endpoint especializado POST /api/v1/dispatch/process-orders/truck-load."""
    res_mock = client.get("/api/v1/dispatch/mock-orders")
    orders_payload = res_mock.json()

    res = client.post(
        "/api/v1/dispatch/process-orders/truck-load",
        json={"pedidos": orders_payload}
    )
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "SUCESSO"
    assert "total_viagens" in data
    assert "viagens" in data
    assert len(data["viagens"]) > 0

    viagem_1 = data["viagens"][0]
    assert "pedidos_carroceria" in viagem_1
    primeiro_pedido = viagem_1["pedidos_carroceria"][0]
    assert "ordem_carregamento" in primeiro_pedido
    assert "posicao_carroceria" in primeiro_pedido
    assert len(primeiro_pedido["itens"]) > 0


def test_process_orders_delivery_route_endpoint():
    """Valida o endpoint especializado POST /api/v1/dispatch/process-orders/delivery-route."""
    res_mock = client.get("/api/v1/dispatch/mock-orders")
    orders_payload = res_mock.json()

    res = client.post(
        "/api/v1/dispatch/process-orders/delivery-route",
        json={"pedidos": orders_payload}
    )
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "SUCESSO"
    assert "viagens" in data
    viagem_1 = data["viagens"][0]
    assert "paradas" in viagem_1
    primeira_parada = viagem_1["paradas"][0]
    assert primeira_parada["parada"] == 1
    assert "endereco_completo" in primeira_parada
    assert len(primeira_parada["itens"]) > 0
