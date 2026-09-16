"""Testes de integração para emissão de PDFs operacionais.

Valida os dois relatórios obrigatórios:
1. Mapa de Carregamento de Doca (Ordem LIFO / Estivagem no Caminhão)
2. Roteiro de Entregas Otimizado (Ordem do Caixeiro Viajante - TSP)
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.report_service import ReportService

client = TestClient(app)


@pytest.fixture
def mock_trip_payload():
    return {
        "trip_id": "eixo-4-norte-serra-V1",
        "trip_number": 1,
        "trip_title": "Viagem 1 (Primeira Saída)",
        "axis_id": "eixo-4-norte-serra",
        "axis_name": "Norte e Serra",
        "vehicle_id": "accelo-815-01",
        "vehicle_name": "Mercedes-Benz Accelo 815",
        "vehicle_plate": "NBL-8151",
        "total_orders": 3,
        "total_value": 7800.0,
        "total_weight_kg": 3800.0,
        "total_volume_m3": 2.85,
        "weight_occupancy": 79.2,
        "volume_occupancy": 15.4,
        "limiting_resource": "PESO",
        "estimated_tortuosity_distance_km": 142.45,
        "has_long_items": True,
        "items": [
            {
                "id": "L401",
                "external_id": "MOCK-E4-01",
                "city_name": "IPAPORANGA",
                "address_line": "Rua Franklin José Vieira, 100, Centro",
                "weight_kg": 2300.0,
                "volume_m3": 1.62,
                "value": 4800.0,
                "delivery_order": 2,
                "loading_order": 2,
                "has_long_items": False,
                "is_mandatory": True,
                "payment_on_delivery": None,
            },
            {
                "id": "L402",
                "external_id": "MOCK-E4-02",
                "city_name": "IPAPORANGA",
                "address_line": "Av. 22 de Setembro, 240",
                "weight_kg": 7.5,
                "volume_m3": 0.12,
                "value": 1500.0,
                "delivery_order": 1,
                "loading_order": 3,
                "has_long_items": True,
                "is_mandatory": True,
                "payment_on_delivery": "A RECEBER",
            },
            {
                "id": "L404",
                "external_id": "MOCK-E4-04",
                "city_name": "PORANGA",
                "address_line": "Rua do Comércio, 310",
                "weight_kg": 1492.5,
                "volume_m3": 1.11,
                "value": 1500.0,
                "delivery_order": 3,
                "loading_order": 1,
                "has_long_items": False,
                "is_mandatory": False,
                "payment_on_delivery": None,
            },
        ]
    }


def test_report_service_loading_sheet(mock_trip_payload):
    """Valida renderização de HTML e compilação do PDF de carregamento na doca."""
    html_str = ReportService.render_loading_sheet_html(mock_trip_payload)
    assert "MAPA DE CARREGAMENTO DE DOCA (ESTIVAGEM LIFO)" in html_str
    assert "1º (FUNDO)" in html_str
    assert "PORTA" in html_str
    assert "TUBOS/BARRAS DE 6 METROS" in html_str
    assert "Conferente de Expedição / Doca" in html_str

    pdf_bytes = ReportService.generate_loading_sheet_pdf(mock_trip_payload)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")


def test_report_service_delivery_route(mock_trip_payload):
    """Valida renderização de HTML e compilação do PDF de roteiro de entregas TSP."""
    html_str = ReportService.render_delivery_route_html(mock_trip_payload)
    assert "ROTEIRO DE ENTREGAS OTIMIZADO (ALGORITMO DO CAIXEIRO VIAJANTE - TSP)" in html_str
    assert "1ª" in html_str
    assert "A RECEBER" in html_str
    assert "Assinatura Cliente" in html_str
    assert "142.5 km" in html_str or "142.4" in html_str

    pdf_bytes = ReportService.generate_delivery_route_pdf(mock_trip_payload)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")


def test_api_load_plan_pdf_and_html_endpoints():
    """Valida os endpoints REST de emissão dos dois documentos a partir de um plano otimizado."""
    # 1. Cria um plano de carga para o Eixo 4
    opt_res = client.post(
        "/api/v1/load-plans/optimize",
        json={
            "axis_id": "eixo-4-norte-serra",
            "vehicle_id": "accelo-815-01",
        }
    )
    assert opt_res.status_code == 200
    plan_id = opt_res.json()["id"]

    # 2. Testa Mapa de Carregamento (PDF e HTML)
    res_loading_pdf = client.get(f"/api/v1/load-plans/{plan_id}/loading-sheet/pdf")
    assert res_loading_pdf.status_code == 200
    assert res_loading_pdf.headers["content-type"] == "application/pdf"
    assert res_loading_pdf.content.startswith(b"%PDF-")

    res_loading_html = client.get(f"/api/v1/load-plans/{plan_id}/loading-sheet/html")
    assert res_loading_html.status_code == 200
    assert "text/html" in res_loading_html.headers["content-type"]
    assert "MAPA DE CARREGAMENTO DE DOCA" in res_loading_html.text

    # 3. Testa Roteiro de Entregas TSP (PDF e HTML)
    res_route_pdf = client.get(f"/api/v1/load-plans/{plan_id}/delivery-route/pdf")
    assert res_route_pdf.status_code == 200
    assert res_route_pdf.headers["content-type"] == "application/pdf"
    assert res_route_pdf.content.startswith(b"%PDF-")

    res_route_html = client.get(f"/api/v1/load-plans/{plan_id}/delivery-route/html")
    assert res_route_html.status_code == 200
    assert "text/html" in res_route_html.headers["content-type"]
    assert "ROTEIRO DE ENTREGAS OTIMIZADO" in res_route_html.text

    # 4. Testa Retrocompatibilidade com /manifest/pdf
    res_manifest = client.get(f"/api/v1/load-plans/{plan_id}/manifest/pdf")
    assert res_manifest.status_code == 200
    assert res_manifest.headers["content-type"] == "application/pdf"
    assert res_manifest.content.startswith(b"%PDF-")


def test_api_dispatch_trip_pdf_endpoints(mock_trip_payload):
    """Valida os endpoints de PDF de viagens geradas pelo pipeline diário."""
    # 1. Carregamento de Doca
    res_loading = client.post(
        "/api/v1/dispatch/trips/loading-sheet/pdf",
        json=mock_trip_payload
    )
    assert res_loading.status_code == 200
    assert res_loading.headers["content-type"] == "application/pdf"
    assert res_loading.content.startswith(b"%PDF-")

    # 2. Roteiro de Entregas TSP
    res_route = client.post(
        "/api/v1/dispatch/trips/delivery-route/pdf",
        json=mock_trip_payload
    )
    assert res_route.status_code == 200
    assert res_route.headers["content-type"] == "application/pdf"
    assert res_route.content.startswith(b"%PDF-")
