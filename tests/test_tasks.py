import pytest
from tasks.whale_alerts import should_alert
from tasks.price_alerts import is_new_ath, is_volume_spike

def test_should_alert_above_threshold():
    assert should_alert(usd_value=600, threshold=500) is True

def test_should_alert_below_threshold():
    assert should_alert(usd_value=400, threshold=500) is False

def test_is_new_ath_when_no_existing():
    assert is_new_ath(current_price=0.001, ath=None) is True

def test_is_new_ath_when_higher():
    ath = {"price": 0.0005, "market_cap": 5000}
    assert is_new_ath(current_price=0.001, ath=ath) is True

def test_is_not_new_ath_when_lower():
    ath = {"price": 0.002, "market_cap": 20000}
    assert is_new_ath(current_price=0.001, ath=ath) is False

def test_volume_spike_detected():
    assert is_volume_spike(current_vol=12000, avg_vol=5000, multiple=2.0) is True

def test_volume_spike_not_triggered():
    assert is_volume_spike(current_vol=8000, avg_vol=5000, multiple=2.0) is False

def test_volume_spike_zero_avg_no_crash():
    assert is_volume_spike(current_vol=1000, avg_vol=0, multiple=2.0) is False
