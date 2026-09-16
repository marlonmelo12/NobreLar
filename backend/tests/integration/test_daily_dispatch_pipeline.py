"""Testes de integração do pipeline de faturamento diário e alocação multi-viagens com dados reais."""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.services.dispatch_pipeline import DailyDispatchPipeline
from app.core.config import settings

client = TestClient(app)


def test_process_daily_billing_pipeline():
    """Valida o processamento completo de um lote de faturamento com pedidos reais da Nobre Lar."""
    pipeline = DailyDispatchPipeline()
    real_csv = settings.DATA_RAW_DIR / "Pedidos_Filtrados_Semana_1_Anonimizado (1).csv"

    res = pipeline.process_daily_billing(
        csv_file_path_or_df=real_csv,
        profile_name="Equilibrado",
        time_limit_seconds=15.0
    )

    assert res["status"] == "SUCESSO"
    summary = res["summary"]
    assert summary["total_records_read"] > 0
    assert summary["total_trips_generated"] >= 1

    for trip in res["trips"]:
        assert trip["total_weight_kg"] <= 4800.0, f"Viagem {trip['trip_id']} não pode violar 4.800 kg."
        assert trip["total_volume_m3"] <= 18.50, f"Viagem {trip['trip_id']} não pode violar 18,5 m³."
        assert trip["is_valid"] is True
        for item in trip["items"]:
            assert "loading_order" in item, "Cada pedido deve ter sua sequência LIFO de doca."
            assert "delivery_order" in item, "Cada pedido deve ter sua ordem de entrega definida."


def test_api_dispatch_upload_csv():
    """Valida o endpoint REST POST /api/v1/dispatch/daily-pipeline via upload de arquivo multipart com dados reais."""
    real_csv = settings.DATA_RAW_DIR / "Pedidos_Filtrados_Semana_1_Anonimizado (1).csv"
    with open(real_csv, "rb") as f:
        response = client.post(
            "/api/v1/dispatch/daily-pipeline",
            files={"file": ("pedidos_semana_1.csv", f, "text/csv")},
            data={"profile_name": "Equilibrado", "time_limit_seconds": 15.0}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCESSO"
    assert data["summary"]["total_trips_generated"] >= 1
