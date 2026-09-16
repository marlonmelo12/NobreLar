"""Testes de integração para validação de restrições territoriais da frota.

Garante que os veículos menores (Kia Bongo e Hyundai HR) fiquem estritamente
restritos a Crateús e seus distritos, bloqueando despacho para cidades externas.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_intermunicipal_axis_rejects_kia_bongo():
    """Valida que o Kia Bongo é compulsoriamente bloqueado no Eixo 4 (Ipaporanga/Poranga)."""
    response = client.post(
        "/api/v1/load-plans/optimize",
        json={
            "axis_id": "eixo-4-norte-serra",
            "vehicle_id": "kia-bongo-01",
            "time_limit_seconds": 10.0
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert "Incompatibilidade operacional" in data["detail"]
    assert "restrito ao município de Crateús" in data["detail"]


def test_intermunicipal_axis_rejects_hyundai_hr():
    """Valida que o Hyundai HR é compulsoriamente bloqueado no Eixo 2 (Sertão Central)."""
    response = client.post(
        "/api/v1/load-plans/optimize",
        json={
            "axis_id": "eixo-2-sertao-central",
            "vehicle_id": "hyundai-hr-01",
            "time_limit_seconds": 10.0
        }
    )
    assert response.status_code == 422
    data = response.json()
    assert "Incompatibilidade operacional" in data["detail"]
    assert "restrito ao município de Crateús" in data["detail"]


def test_intermunicipal_axis_accepts_accelo_815():
    """Valida que o caminhão maior (Mercedes Accelo 815) é aceito para o Eixo 4."""
    response = client.post(
        "/api/v1/load-plans/optimize",
        json={
            "axis_id": "eixo-4-norte-serra",
            "vehicle_id": "accelo-815-01",
            "time_limit_seconds": 10.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_id"] == "accelo-815-01"
    assert data["total_weight_kg"] <= 4800.0
    assert data["total_volume_m3"] <= 18.50
