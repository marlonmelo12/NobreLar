"""Testes de integração para a API desacoplada, carroceria aberta e drill-down de itens.

Valida os contratos JSON estruturados baseados no modelo de pedido da Nobre Lar (N. L12608361).
"""

import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


SAMPLE_ORDERS = [
    {
        "id": "L12608361",
        "data": "16/09/2026",
        "cliente": "Cliente Teste Nobre Lar 1",
        "cidade": "CRATEUS",
        "endereco": "Rua Dom Pedro II, 450, Centro",
        "valor": 810.00,
        "urgente": False,
        "situacao": "NORMAL",
        "itens": [
            {"codigo": "23717", "descricao": "TUBO PVC ESGOTO 100MM", "quantidade": 5.0, "unidade": "MT", "preco_unitario": 35.0},
            {"codigo": "21243", "descricao": "PISO CERBRAS IPANEMA BEGE 46 X 46 A", "quantidade": 25.30, "unidade": "MT", "preco_unitario": 20.0},
            {"codigo": "1001", "descricao": "CIMENTO POTY TODAS AS OBRAS 50KG", "quantidade": 10.0, "unidade": "SC", "preco_unitario": 36.0}
        ]
    },
    {
        "id": "L12608362",
        "data": "16/09/2026",
        "cliente": "Cliente Urgente Norte",
        "cidade": "IPAPORANGA",
        "endereco": "Av. Central, 120",
        "valor": 1200.00,
        "urgente": True,
        "situacao": "URGENTE",
        "itens": [
            {"codigo": "1001", "descricao": "CIMENTO POTY TODAS AS OBRAS 50KG", "quantidade": 20.0, "unidade": "SC", "preco_unitario": 36.0}
        ]
    },
    {
        "id": "L12608998",
        "data": "16/09/2026",
        "cliente": "Cliente Balcao",
        "cidade": "CRATEUS",
        "endereco": "Balcão Loja",
        "valor": 150.00,
        "urgente": False,
        "situacao": "RETIRADA",
        "itens": [
            {"codigo": "500", "descricao": "FITA ISOLANTE 20M", "quantidade": 2.0, "unidade": "UN", "preco_unitario": 10.0}
        ]
    },
    {
        "id": "L12608999",
        "data": "16/09/2026",
        "cliente": "Cliente Desistente",
        "cidade": "CRATEUS",
        "endereco": "Rua B, 20",
        "valor": 300.00,
        "urgente": False,
        "situacao": "CANCELADO",
        "itens": [
            {"codigo": "600", "descricao": "TINTA ACRILICA 18L", "quantidade": 1.0, "unidade": "LT", "preco_unitario": 300.0}
        ]
    }
]


def test_process_orders_decoupled_full():
    """Valida o endpoint POST /api/v1/dispatch/process-orders com drill-down e carroceria aberta."""
    res = client.post(
        "/api/v1/dispatch/process-orders",
        json={"pedidos": SAMPLE_ORDERS, "perfil_otimizacao": "Equilibrado"}
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


def test_post_orders_then_get_load_and_route():
    """Valida a arquitetura estrita: POST único para enviar pedidos e GET exclusivo para consultar carga e rota."""
    # 1. POST único para submissão do JSON de pedidos
    res_post = client.post(
        "/api/v1/dispatch/orders",
        json={"pedidos": SAMPLE_ORDERS, "perfil_otimizacao": "Equilibrado"}
    )
    assert res_post.status_code == 200
    data_post = res_post.json()
    assert data_post["status"] == "SUCESSO"
    assert len(data_post["cargas_caminhao"]) > 0

    # 2. GET exclusivo para consultar os dados de carga no caminhão
    res_truck = client.get("/api/v1/dispatch/truck-load")
    assert res_truck.status_code == 200
    data_truck = res_truck.json()
    assert data_truck["status"] == "SUCESSO"
    assert len(data_truck["viagens"]) > 0
    viagem_1 = data_truck["viagens"][0]
    assert "pedidos_carroceria" in viagem_1
    assert len(viagem_1["pedidos_carroceria"]) > 0
    assert len(viagem_1["pedidos_carroceria"][0]["itens"]) > 0

    # 3. GET exclusivo para consultar os dados da rota de entrega (TSP)
    res_route = client.get("/api/v1/dispatch/delivery-route")
    assert res_route.status_code == 200
    data_route = res_route.json()
    assert data_route["status"] == "SUCESSO"
    assert len(data_route["viagens"]) > 0
    viagem_rot = data_route["viagens"][0]
    assert "paradas" in viagem_rot
    assert len(viagem_rot["paradas"]) > 0
    assert "endereco_completo" in viagem_rot["paradas"][0]
    assert len(viagem_rot["paradas"][0]["itens"]) > 0

    # 4. Assegura que POST em /truck-load e /delivery-route não é permitido (apenas GET)
    res_post_truck = client.post("/api/v1/dispatch/truck-load", json={})
    assert res_post_truck.status_code == 405, "Endpoint de carga deve ser estritamente GET"

    res_post_route = client.post("/api/v1/dispatch/delivery-route", json={})
    assert res_post_route.status_code == 405, "Endpoint de rota deve ser estritamente GET"


def test_get_endpoints_and_pdf():
    """Valida os endpoints GET para consulta direta e download de relatórios PDF."""
    # Garante que um lote foi despachado
    client.post(
        "/api/v1/dispatch/orders",
        json={"pedidos": SAMPLE_ORDERS, "perfil_otimizacao": "Equilibrado"}
    )

    # 1. GET /process-orders
    res_proc = client.get("/api/v1/dispatch/process-orders")
    assert res_proc.status_code == 200
    data_proc = res_proc.json()
    assert data_proc["status"] == "SUCESSO"
    assert "cargas_caminhao" in data_proc
    assert "roteiros_entrega" in data_proc

    # 2. GET /trips/default/pdf/loading-sheet
    res_pdf_load = client.get("/api/v1/dispatch/trips/default/pdf/loading-sheet")
    assert res_pdf_load.status_code == 200
    assert res_pdf_load.headers["content-type"] == "application/pdf"
    assert res_pdf_load.content.startswith(b"%PDF-")

    # 3. GET /trips/default/pdf/delivery-route
    res_pdf_route = client.get("/api/v1/dispatch/trips/default/pdf/delivery-route")
    assert res_pdf_route.status_code == 200
    assert res_pdf_route.headers["content-type"] == "application/pdf"
    assert res_pdf_route.content.startswith(b"%PDF-")


def test_single_order_absorption_and_piso_conversion():
    """Valida absorção de pedido único diretamente via POST e conversão de m² de piso para caixas CX."""
    single_order = {
        "id": "PED-UNICO-01",
        "data": "16/09/2026",
        "cliente": "Cliente Teste Único",
        "cidade": "CRATEUS",
        "endereco": "Rua Central, 100",
        "valor": 500.0,
        "urgente": False,
        "situacao": "NORMAL",
        "itens": [
            {
                "codigo": "21243",
                "descricao": "PISO CERBRAS IPANEMA BEGE 46 X 46 A",
                "quantidade": 25.30,
                "unidade": "MT",
                "preco_unitario": 20.0
            }
        ]
    }
    res = client.post("/api/v1/dispatch/orders", json=single_order)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCESSO"
    assert data["resumo"]["total_allocated_orders"] == 1
    assert len(data["cargas_caminhao"]) == 1
    trip = data["cargas_caminhao"][0]
    assert trip["viagem_numero"] == 1
    assert len(trip["pedidos_carroceria"]) == 1
    ped = trip["pedidos_carroceria"][0]
    assert ped["possui_itens_6m"] is False
    assert ped["posicao_carroceria"] is None
    assert len(ped["itens"]) == 1
    piso_item = ped["itens"][0]
    assert piso_item["unidade"] == "CX"
    assert piso_item["quantidade"] == 11.0

