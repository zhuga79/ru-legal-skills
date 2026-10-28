"""Unit tests для rospatent-mcp (v0.2.0 — URL-builder mode).

У ФИПС нет публичного REST API, поэтому tools не ходят в сеть:
они строят проверяемые URL для ручного поиска юристом.
"""

from __future__ import annotations

import pytest

from rospatent_mcp.server import (
    FIPS_PATENT_PORTAL,
    FIPS_TRADEMARK_PORTAL,
    build_patent_search_url,
    build_software_search_url,
    build_trademark_search_url,
    check_attorney_register_url,
    get_patent_card_url,
    get_trademark_card_url,
)

# ---------------------------------------------------------------------------
# Поиск: товарные знаки
# ---------------------------------------------------------------------------


def test_trademark_search_url_encodes_query():
    result = build_trademark_search_url(query="АЛЬФА БЕТА")

    expected = FIPS_TRADEMARK_PORTAL.format(query="%D0%90%D0%9B%D0%AC%D0%A4%D0%90+%D0%91%D0%95%D0%A2%D0%90")
    assert result.url == expected
    assert "niceClass" not in result.url
    assert "АЛЬФА БЕТА" in result.description
    assert "по всем классам" in result.description


def test_trademark_search_url_adds_nice_class():
    result = build_trademark_search_url(query="кофе", nice_class=30)

    assert result.url.endswith("&niceClass=30")
    assert "классе МКТУ 30" in result.description
    assert "new.fips.ru" in result.description


# ---------------------------------------------------------------------------
# Поиск: патенты
# ---------------------------------------------------------------------------


def test_patent_search_url_default_type_is_invention():
    result = build_patent_search_url(query="обработка данных")

    assert FIPS_PATENT_PORTAL.format(query="%D0%BE%D0%B1%D1%80%D0%B0%D0%B1%D0%BE%D1%82%D0%BA%D0%B0+%D0%B4%D0%B0%D0%BD%D0%BD%D1%8B%D1%85") in result.url
    assert "patentType=INVENTION" in result.url


@pytest.mark.parametrize(
    ("patent_type", "expected"),
    [("utility", "UTILITY_MODEL"), ("design", "INDUSTRIAL_DESIGN")],
)
def test_patent_search_url_maps_patent_type(patent_type, expected):
    result = build_patent_search_url(query="устройство", patent_type=patent_type)
    assert f"patentType={expected}" in result.url


def test_patent_search_url_ignores_unknown_type():
    result = build_patent_search_url(query="устройство", patent_type="unknown")
    assert "patentType" not in result.url


# ---------------------------------------------------------------------------
# Карточки реестров
# ---------------------------------------------------------------------------


def test_trademark_card_url_strips_prefix():
    result = get_trademark_card_url(registration_number="№762341")

    assert result.register_type == "RUTM"
    assert result.registration_number == "762341"
    assert "rn=762341" in result.url
    assert "RUTM" in result.description


def test_trademark_card_url_rejects_non_numeric():
    with pytest.raises(ValueError, match="должен быть числом"):
        get_trademark_card_url(registration_number="A-762341")


def test_patent_card_url_strips_ru_prefix():
    result = get_patent_card_url(registration_number="RU 2742123")

    assert result.register_type == "RUPAT"
    assert result.registration_number == "2742123"
    assert "rn=2742123" in result.url


def test_patent_card_url_rejects_non_numeric():
    with pytest.raises(ValueError, match="должен быть числом"):
        get_patent_card_url(registration_number="патент")


# ---------------------------------------------------------------------------
# Программы для ЭВМ и патентные поверенные
# ---------------------------------------------------------------------------


def test_software_search_url_uses_evm_register():
    result = build_software_search_url(query="CRM система")

    assert "type=EVM" in result.url
    assert "query=CRM+%D1%81%D0%B8%D1%81%D1%82%D0%B5%D0%BC%D0%B0" in result.url
    assert "CRM система" in result.description


def test_attorney_register_url_without_name():
    result = check_attorney_register_url()

    assert result.url.endswith("patent-attorneys.html")
    assert "Ctrl+F" in result.note


def test_attorney_register_url_with_name():
    result = check_attorney_register_url(attorney_name="Иванов Иван")

    assert "?search=" in result.url
    assert "Иванов Иван" in result.note
