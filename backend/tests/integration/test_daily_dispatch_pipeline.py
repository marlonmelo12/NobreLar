"""Testes de integração do pipeline de faturamento diário e alocação multi-viagens."""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.services.dispatch_pipeline import DailyDispatchPipeline
from app.core.config import settings

client = TestClient(app)


def test_simulate_daily_mock_pipeline():
    """Valida o processamento completo de um dia de faturamento com o mock oficial."""
    pipeline = DailyDispatchPipeline()
    mock_csv = settings.DATA_RAW_DIR / "mock_faturamento_diario.csv"

    res = pipeline.process_daily_billing(
        csv_file_path_or_df=mock_csv,
        profile_name="Equilibrado",
        time_limit_seconds=15.0
    )

    assert res["status"] == "SUCESSO"
    summary = res["summary"]

    # 1. Validação do Filtro de Limpeza (Balcão e Cancelados)
    # MOCK-B01 (Retirada), MOCK-B02 (Cancelado), MOCK-B03 (Retirada) devem ser descartados
    discarded = res["discarded_cleaning_logs"]
    discarded_refs = [d["pedido"] for d in discarded]
    assert "MOCK-B01" in discarded_refs, "Venda balcão MOCK-B01 deve ser descartada pelo filtro."
    assert "MOCK-B02" in discarded_refs, "Pedido cancelado MOCK-B02 deve ser descartado pelo filtro."
    assert "MOCK-B03" in discarded_refs, "Venda balcão MOCK-B03 deve ser descartada pelo filtro."
    assert summary["total_discarded_cleaning"] >= 3

    # 2. Validação de Múltiplas Viagens no Eixo 4 (Norte e Serra)
    # A demanda total do Eixo 4 excede a capacidade do caminhão (4.800 kg / 18,5 m³)
    eixo4_trips = [t for t in res["trips"] if t["axis_id"] == "eixo-4-norte-serra"]
    assert len(eixo4_trips) >= 2, "A sobrecarga do Eixo 4 deve gerar compulsoriamente pelo menos 2 viagens (Viagem 1 e Viagem 2)."

    trip1 = next(t for t in eixo4_trips if t["trip_number"] == 1)
    trip2 = next(t for t in eixo4_trips if t["trip_number"] == 2)

    # Ambas as viagens devem cumprir as invariantes físicas de 4.800 kg e 18,5 m³
    assert trip1["total_weight_kg"] <= 4800.0, "Viagem 1 do Eixo 4 não pode violar 4.800 kg."
    assert trip1["total_volume_m3"] <= 18.50, "Viagem 1 do Eixo 4 não pode violar 18,5 m³."
    assert trip1["is_valid"] is True

    assert trip2["total_weight_kg"] <= 4800.0, "Viagem 2 do Eixo 4 não pode violar 4.800 kg."
    assert trip2["total_volume_m3"] <= 18.50, "Viagem 2 do Eixo 4 não pode violar 18,5 m³."
    assert trip2["is_valid"] is True

    # 3. Priorização Compulsória de Pedidos Urgentes
    # MOCK-E4-01 e MOCK-E4-02 possuem flag URGENTE e devem estar na Viagem 1
    trip1_order_ids = [it["id"] for it in trip1["items"]]
    trip1_ext_ids = [it.get("external_id") for it in trip1["items"]]
    assert "L401" in trip1_order_ids or "MOCK-E4-01" in trip1_ext_ids, "Pedido urgente MOCK-E4-01 deve ser priorizado na Viagem 1."
    assert "L402" in trip1_order_ids or "MOCK-E4-02" in trip1_ext_ids, "Pedido urgente com tubo 6m MOCK-E4-02 deve ser priorizado na Viagem 1."

    # 4. Sequenciamento LIFO e Rota TSP
    for t in res["trips"]:
        for item in t["items"]:
            assert "loading_order" in item, "Cada pedido deve ter sua sequência LIFO de doca."
            assert "delivery_order" in item, "Cada pedido deve ter sua ordem de entrega definida."


def test_api_dispatch_simulate_mock_endpoint():
    """Valida o endpoint REST POST /api/v1/dispatch/simulate-mock."""
    response = client.post("/api/v1/dispatch/simulate-mock")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCESSO"
    assert "trips" in data
    assert len(data["trips"]) > 0


def test_api_dispatch_upload_csv():
    """Valida o endpoint REST POST /api/v1/dispatch/daily-pipeline via upload de arquivo multipart."""
    mock_csv = settings.DATA_RAW_DIR / "mock_faturamento_diario.csv"
    with open(mock_csv, "rb") as f:
        response = client.post(
            "/api/v1/dispatch/daily-pipeline",
            files={"file": ("faturamento_hoje.csv", f, "text/csv")},
            data={"profile_name": "Equilibrado", "time_limit_seconds": 15.0}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCESSO"
    assert data["summary"]["total_trips_generated"] >= 2
