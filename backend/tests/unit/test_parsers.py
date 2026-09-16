"""Testes unitários para o módulo de parsers e sanitizadores."""

import pytest
from app.services.parsers import (
    clean_currency,
    sanitize_order_id,
    sanitize_brazilian_date,
    parse_order_items,
    parse_address_components
)


def test_clean_currency():
    """Valida conversão de moeda brasileira para float."""
    assert clean_currency("R$ 1.328,97") == 1328.97
    assert clean_currency("R$ 412,00") == 412.00
    assert clean_currency("91,60") == 91.60
    assert clean_currency(None) == 0.0
    assert clean_currency("nan") == 0.0
    assert clean_currency("") == 0.0


def test_sanitize_order_id():
    """Valida padronização de IDs de pedidos para o formato L{dígitos}."""
    assert sanitize_order_id("12.608570") == "L12608570"
    assert sanitize_order_id("L12609716.") == "L12609716"
    assert sanitize_order_id("8507035") == "L8507035"
    assert sanitize_order_id("L12608278") == "L12608278"
    assert sanitize_order_id(None) == "INVALIDO"


def test_sanitize_brazilian_date():
    """Valida correção de datas históricas corrompidas para formato ISO 8601."""
    assert sanitize_brazilian_date("01/08/2026") == "2026-08-01"
    assert sanitize_brazilian_date("01/08/26") == "2026-08-01"
    # Erros históricos da base
    assert sanitize_brazilian_date("26/08/14") == "2026-08-26"
    assert sanitize_brazilian_date("15/0826") == "2026-08-15"
    assert sanitize_brazilian_date("20/0826") == "2026-08-20"
    assert sanitize_brazilian_date("28/0/26") == "2026-08-28"
    assert sanitize_brazilian_date("290826") == "2026-08-29"


def test_parse_order_items():
    """Valida extração estruturada de itens a partir de string agregada com regex."""
    raw = (
        '12185 - CX. DAGUA BAKOF 1000L C/TMP (1,00 UN) | '
        '21503 - CIMENTO POTY TODAS OBRAS 50KG (80,00 UN) | '
        '21243 - PISO CERBRAS IPANEMA BEGE 46 X 46 "A" (25,30 MT)'
    )
    items = parse_order_items(raw)
    assert len(items) == 3

    assert items[0]["product_code"] == "12185"
    assert "BAKOF" in items[0]["product_desc"]
    assert items[0]["quantity"] == 1.0
    assert items[0]["unit"] == "UN"

    assert items[1]["product_code"] == "21503"
    assert items[1]["quantity"] == 80.0
    assert items[1]["unit"] == "UN"

    assert items[2]["product_code"] == "21243"
    assert items[2]["quantity"] == 25.30
    assert items[2]["unit"] == "MT"


def test_parse_address_components():
    """Valida extração de CEP, número e bairro de endereços livres."""
    addr = "Rua Coronel Zezé, 1420, Bairro Centro, Crateús - CE, 63700-000"
    res = parse_address_components(addr)
    assert res["address_number"] == "1420"
    assert res["postal_code"] == "63700-000"
    assert "Centro" in (res["neighborhood"] or "")
