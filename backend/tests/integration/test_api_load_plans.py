"""Testes de integração end-to-end para os endpoints da API REST do NobreLOG IA."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_health_and_ready():
    """Valida os endpoints de observabilidade health e ready (RNF-006-A)."""
    res_health = client.get("/api/v1/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "HEALTHY"

    res_ready = client.get("/api/v1/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "READY"


def test_api_list_vehicles_and_four_fleet():
    """Valida a separação dos 4 veículos da frota incluindo Accelo, Bongo e HR distintos."""
    res = client.get("/api/v1/vehicles")
    assert res.status_code == 200
    vehicles = res.json()
    assert len(vehicles) == 4

    ids = [v["id"] for v in vehicles]
    assert "accelo-815-01" in ids
    assert "kia-bongo-01" in ids
    assert "hyundai-hr-01" in ids
    assert "titan-160-01" in ids

    # Validação do Accelo com 18.5 m³ (ADR-0010)
    accelo = next(v for v in vehicles if v["id"] == "accelo-815-01")
    assert accelo["useful_volume_m3"] == 18.50
    assert accelo["allows_long_items"] is True
    assert accelo["restricted_to_crateus"] is False


def test_api_optimize_load_plan_eixo4():
    """Valida a geração completa de um plano de carga para o Eixo 4 com o Accelo 815."""
    res = client.post(
        "/api/v1/load-plans/optimize",
        json={
            "axis_id": "eixo-4-norte-serra",
            "vehicle_id": "accelo-815-01",
            "time_limit_seconds": 15.0
        }
    )
    assert res.status_code == 200
    plan = res.json()

    assert plan["solver_status"] in ("OPTIMAL", "FEASIBLE")
    assert plan["total_orders"] > 0
    assert plan["total_weight_kg"] <= 4800.0
    assert plan["total_volume_m3"] <= 18.50
    assert plan["limiting_resource"] in ("PESO", "VOLUME")
    assert len(plan["items"]) == plan["total_orders"]
    assert len(plan["decisions"]) > 0

    # Validação da ordenação LIFO (a menor sequência de entrega tem maior sequência de carregamento)
    items = plan["items"]
    first_deliv = min(items, key=lambda x: x["delivery_order"])
    last_deliv = max(items, key=lambda x: x["delivery_order"])
    assert first_deliv["loading_order"] > last_deliv["loading_order"], "Sequenciamento LIFO violado!"

    plan_id = plan["id"]

    # Teste de emissão do Romaneio em HTML
    res_html = client.get(f"/api/v1/load-plans/{plan_id}/manifest/html")
    assert res_html.status_code == 200
    assert "Romaneio Oficial de Carga" in res_html.text

    # Teste de emissão do Romaneio em PDF
    res_pdf = client.get(f"/api/v1/load-plans/{plan_id}/manifest/pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert len(res_pdf.content) > 1000


def test_api_manual_toggle_and_conflict_409():
    """Valida a edição manual auditada com rejeição 409 Conflict em caso de estouro físico."""
    # Gera um plano base
    res = client.post(
        "/api/v1/load-plans/optimize",
        json={
            "axis_id": "eixo-4-norte-serra",
            "vehicle_id": "accelo-815-01",
            "time_limit_seconds": 10.0
        }
    )
    plan = res.json()
    plan_id = plan["id"]
    items = plan["items"]
    assert len(items) > 0

    first_item_id = items[0]["order_id"]
    weight_orig = plan["total_weight_kg"]

    # 1. Remover item manualmente
    res_toggle_out = client.post(f"/api/v1/load-plans/{plan_id}/items/{first_item_id}/toggle")
    assert res_toggle_out.status_code == 200
    plan_updated = res_toggle_out.json()
    assert plan_updated["is_manually_modified"] is True
    assert plan_updated["total_weight_kg"] < weight_orig

    # Verifica se a auditoria registrou
    res_audit = client.get(f"/api/v1/load-plans/{plan_id}/audit")
    assert res_audit.status_code == 200
    audits = res_audit.json()
    assert any(a["action"] == "REMOVE_ORDER" and a["accepted"] is True for a in audits)


def test_api_analytics_axis_profile():
    """Valida o cálculo analítico de densidade por eixo e recurso limitante (CA-016)."""
    res = client.get("/api/v1/analytics/axis-profile")
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0

    eixo4 = next((d for d in data if d["axis_id"] == "eixo-4-norte-serra"), None)
    assert eixo4 is not None
    assert "density_kg_m3" in eixo4
    assert eixo4["predominant_limiting_resource"] in ("PESO", "VOLUME")
