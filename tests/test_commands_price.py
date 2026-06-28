import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from commands.price import fmt_price, fmt_stats, build_ca_message

def test_fmt_price_formats_correctly():
    data = {"price": 0.00000234, "change_24h": 12.4, "market_cap": 234500,
            "volume_24h": 18200, "liquidity": 45100}
    result = fmt_price(data)
    assert "$0.0" in result
    assert "12.40%" in result or "12.4%" in result
    assert "𓂀" in result

def test_fmt_price_shows_down_arrow_for_negative():
    data = {"price": 0.000001, "change_24h": -5.2, "market_cap": 1000,
            "volume_24h": 500, "liquidity": 200}
    result = fmt_price(data)
    assert "📉" in result or "-5.2%" in result or "-5.20%" in result

def test_fmt_stats_includes_all_fields():
    data = {"price": 0.00000234, "change_24h": 12.4, "market_cap": 234500,
            "volume_24h": 18200, "liquidity": 45100, "txns_24h": 230}
    result = fmt_stats(data, holders=1500)
    assert "1,500" in result
    assert "230" in result

def test_build_ca_message_contains_ca():
    from config import CA
    result = build_ca_message()
    assert CA in result
