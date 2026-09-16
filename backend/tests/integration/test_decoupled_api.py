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
    assert ped_oficial["situacao"] == "NORMAL"
    assert "situacao_entrega" not in ped_oficial, "Campo legado situacao_entrega não deve existir"
    assert len(ped_oficial["itens"]) == 3
    assert ped_oficial["itens"][0]["codigo"] == "23717"
    assert ped_oficial["itens"][0]["unidade"] == "MT"

    # Garante que todos os pedidos usam o enum canônico e não contêm situacao_entrega
    enum_validos = {"NORMAL", "URGENTE", "RETIRADA", "CARRO HORARIO", "PROGRAMADO", "TOPIQUE", "CANCELADO"}
    for o in orders:
        assert "situacao_entrega" not in o
        assert o["situacao"] in enum_validos


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

    # 1. Validação de Descartes de Limpeza (Balcão e Cancelado via campo situacao)
    descartes = data["descartes_limpeza"]
    pedidos_descartados = [d["pedido"] for d in descartes]
    assert "L12608998" in pedidos_descartados, "Pedido com situacao RETIRADA balcão deve ser descartado"
    assert "L12608999" in pedidos_descartados, "Pedido com situacao CANCELADO deve ser descartado"

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
            assert "situacao" in ped
            assert "situacao_entrega" not in ped
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
            assert "situacao" in parada
            assert "situacao_entrega" not in parada
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


def test_get_endpoints_for_frontend():
    """Valida que o Frontend pode consultar cargas, rotas e PDFs diretamente via GET sem body."""
    # 1. GET /truck-load
    res_truck = client.get("/api/v1/dispatch/truck-load")
    assert res_truck.status_code == 200
    data_truck = res_truck.json()
    assert data_truck["status"] == "SUCESSO"
    assert len(data_truck["viagens"]) > 0
    assert "pedidos_carroceria" in data_truck["viagens"][0]

    # 2. GET /delivery-route
    res_route = client.get("/api/v1/dispatch/delivery-route")
    assert res_route.status_code == 200
    data_route = res_route.json()
    assert data_route["status"] == "SUCESSO"
    assert len(data_route["viagens"]) > 0
    assert "paradas" in data_route["viagens"][0]

    # 3. GET /process-orders
    res_proc = client.get("/api/v1/dispatch/process-orders")
    assert res_proc.status_code == 200
    data_proc = res_proc.json()
    assert data_proc["status"] == "SUCESSO"
    assert "cargas_caminhao" in data_proc
    assert "roteiros_entrega" in data_proc

    # 4. GET /trips/default/pdf/loading-sheet
    res_pdf_load = client.get("/api/v1/dispatch/trips/default/pdf/loading-sheet")
    assert res_pdf_load.status_code == 200
    assert res_pdf_load.headers["content-type"] == "application/pdf"
    assert res_pdf_load.content.startswith(b"%PDF-")

    # 5. GET /trips/default/pdf/delivery-route
    res_pdf_route = client.get("/api/v1/dispatch/trips/default/pdf/delivery-route")
    assert res_pdf_route.status_code == 200
    assert res_pdf_route.headers["content-type"] == "application/pdf"
    assert res_pdf_route.content.startswith(b"%PDF-")
