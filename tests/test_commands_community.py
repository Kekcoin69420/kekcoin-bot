import pytest
from commands.community import calc_moonmath, calc_hodlcheck, get_random_kek

def test_moonmath_calculates_correctly():
    # At $1M MC with 1B supply, price = $0.001. 1000 tokens = $1.00
    result = calc_moonmath(amount=1000, target_mc=1_000_000, total_supply=1_000_000_000)
    assert result == pytest.approx(1.00)

def test_hodlcheck_gain():
    result = calc_hodlcheck(entry=0.000001, current=0.000002)
    assert result == pytest.approx(100.0)  # 100% gain

def test_hodlcheck_loss():
    result = calc_hodlcheck(entry=0.000002, current=0.000001)
    assert result == pytest.approx(-50.0)  # 50% loss

def test_get_random_kek_returns_string():
    msg = get_random_kek()
    assert isinstance(msg, str)
    assert len(msg) > 10
