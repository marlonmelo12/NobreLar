"""Testes unitários para o serviço de cubagem técnica e fallback heurístico."""

import pytest
from app.services.cubagem_service import CubagemService


@pytest.fixture
def cubagem_svc():
    return CubagemService()


def test_top85_cimento_poty(cubagem_svc):
    """Valida cubagem do cimento Poty 50kg constante no Top 85 (código 21503)."""
    res = cubagem_svc.compute_item_cubing(
        product_code="21503",
        product_desc="CIMENTO POTY TODAS OBRAS 50KG",
        quantity=10.0,
        unit="UN"
    )
    assert res["computed_weight_kg"] == 500.0
    assert res["computed_volume_m3"] == 0.36
    assert res["cubing_source"] == "ranking_top85"
    assert res["has_long_items"] is False


def test_piso_conversion_m2_to_boxes(cubagem_svc):
    """Valida conversão conservadora de m² para caixas inteiras via math.ceil (RF-006)."""
    # 21243: PISO CERBRAS IPANEMA BEGE 46 X 46 "A", m2_per_box = 2.30 m², peso por caixa = 28.28 kg
    res = cubagem_svc.compute_item_cubing(
        product_code="21243",
        product_desc='PISO CERBRAS IPANEMA BEGE 46 X 46 "A"',
        quantity=25.30,  # 25.30 / 2.30 = 11 caixas exatas
        unit="MT"
    )
    assert res["effective_quantity"] == 11.0
    assert res["effective_unit"] == "CX"
    assert res["computed_weight_kg"] == round(11.0 * 28.28, 2)


def test_piso_conversion_fractional_ceil(cubagem_svc):
    """Valida que fração de m² arredonda para cima em caixas inteiras."""
    res = cubagem_svc.compute_item_cubing(
        product_code="21243",
        product_desc='PISO CERBRAS IPANEMA BEGE 46 X 46 "A"',
        quantity=3.0,  # 3.0 / 2.30 = 1.304 -> ceil = 2 caixas
        unit="MT"
    )
    assert res["effective_quantity"] == 2.0
    assert res["effective_unit"] == "CX"


def test_fallback_heuristic_connections(cubagem_svc):
    """Valida aplicação de fallback para conexões hidráulicas fora do Top 85."""
    res = cubagem_svc.compute_item_cubing(
        product_code="99999",
        product_desc="JOELHO 90 SOLDAVEL 25MM KRONA",
        quantity=20.0,
        unit="UN"
    )
    assert res["cubing_source"] == "heuristica_conexao"
    assert res["is_estimated"] is True
    assert res["unit_weight_kg"] == 0.05
    assert res["unit_volume_m3"] == 0.0003
    assert res["computed_weight_kg"] == 1.0


def test_deactivation_of_long_items_rule(cubagem_svc):
    """Valida que a regra de 6 metros está desativada para implementação futura."""
    res = cubagem_svc.compute_item_cubing(
        product_code="88888",
        product_desc="TUBO ESGOTO 100MM BARRA 6 METROS KRONA",
        quantity=5.0,
        unit="UN"
    )
    assert res["has_long_items"] is False
    assert res["cubing_source"] == "heuristica_longo"
