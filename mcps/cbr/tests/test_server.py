"""Unit tests для cbr-mcp — офлайн, без обращений к cbr.ru."""

from __future__ import annotations

import pytest
from cbr_mcp import server
from cbr_mcp.server import (
    CACHE_TTL_SECONDS,
    KeyRateRecord,
    _get_cached,
    _set_cached,
    calculate_penalty,
    get_exchange_rates,
)

# ---------------------------------------------------------------------------
# Кэш
# ---------------------------------------------------------------------------


def test_cache_roundtrip():
    _set_cached("test:roundtrip", {"usd": 90.5})

    assert _get_cached("test:roundtrip") == {"usd": 90.5}


def test_cache_missing_key_returns_none():
    assert _get_cached("test:definitely-missing") is None


def test_cache_expires(monkeypatch):
    _set_cached("test:expired", "stale")
    # «Сдвигаем» TTL в прошлое — запись должна считаться просроченной
    monkeypatch.setattr(server, "CACHE_TTL_SECONDS", -1)

    assert _get_cached("test:expired") is None


def test_cache_ttl_is_one_hour():
    assert CACHE_TTL_SECONDS == 3600


# ---------------------------------------------------------------------------
# Валидация аргументов (сеть не требуется — падаем раньше запроса)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_exchange_rates_rejects_bad_date():
    with pytest.raises(ValueError, match="Неверный формат даты"):
        await get_exchange_rates(date_iso="26.10.2026")


@pytest.mark.asyncio
async def test_calculate_penalty_rejects_bad_basis():
    with pytest.raises(ValueError, match="Неверный rate_basis"):
        await calculate_penalty(principal_amount=1000, days_overdue=10, rate_basis="unknown")


@pytest.mark.asyncio
async def test_calculate_penalty_zero_days():
    result = await calculate_penalty(principal_amount=1000, days_overdue=0)

    assert result["penalty"] == 0.0
    assert "Нет дней просрочки" in result["note"]


# ---------------------------------------------------------------------------
# Расчёт пеней (ключевая ставка подменяется)
# ---------------------------------------------------------------------------


@pytest.fixture
def fixed_key_rate(monkeypatch):
    async def fake_key_rate():
        return KeyRateRecord(rate=16.0, effective_date="2026-01-01")

    monkeypatch.setattr(server, "get_key_rate", fake_key_rate)
    return 16.0


@pytest.mark.asyncio
async def test_penalty_tax_formula_one_300(fixed_key_rate):
    # НК ст.75: 100 000 × (16% / 300) × 30 = 1 600.00
    result = await calculate_penalty(principal_amount=100_000, days_overdue=30)

    assert result["penalty"] == 1600.0
    assert result["legal_basis"] == "НК РФ ст.75"
    assert result["key_rate_percent"] == 16.0
    assert result["verified"] == "cbr-mcp:get_key_rate"


@pytest.mark.asyncio
async def test_penalty_civil_formula_one_365(fixed_key_rate):
    # ГК ст.395: 100 000 × (16% / 365) × 30 ≈ 1 315.07
    result = await calculate_penalty(
        principal_amount=100_000, days_overdue=30, rate_basis="refinancing"
    )

    assert result["penalty"] == pytest.approx(1315.07, abs=0.01)
    assert result["legal_basis"] == "ГК РФ ст.395"
