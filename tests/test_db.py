import pytest
from tests.conftest import test_db
import db


def test_init_creates_all_tables(test_db):
    cursor = test_db.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert tables >= {"praise", "ath", "fud_keywords", "strikes", "whale_state", "volume_history", "settings"}


def test_get_praise_count_starts_at_zero(test_db):
    assert db.get_praise(test_db) == 0


def test_increment_praise(test_db):
    db.increment_praise(test_db)
    db.increment_praise(test_db)
    assert db.get_praise(test_db) == 2


def test_get_set_setting(test_db):
    db.set_setting(test_db, "whale_threshold_usd", "1000")
    assert db.get_setting(test_db, "whale_threshold_usd") == "1000"


def test_get_setting_returns_default_when_missing(test_db):
    assert db.get_setting(test_db, "nonexistent", default="fallback") == "fallback"


def test_add_and_list_fud_keywords(test_db):
    db.add_fud_keyword(test_db, "scam", added_by=123)
    db.add_fud_keyword(test_db, "rug", added_by=123)
    keywords = db.list_fud_keywords(test_db)
    assert "scam" in keywords
    assert "rug" in keywords


def test_remove_fud_keyword(test_db):
    db.add_fud_keyword(test_db, "dead", added_by=123)
    db.remove_fud_keyword(test_db, "dead")
    assert "dead" not in db.list_fud_keywords(test_db)


def test_add_strike_and_get_count(test_db):
    db.add_strike(test_db, user_id=999, username="badactor")
    db.add_strike(test_db, user_id=999, username="badactor")
    assert db.get_strike_count(test_db, user_id=999) == 2


def test_get_and_set_ath(test_db):
    db.set_ath(test_db, price=0.00001, market_cap=10000.0)
    ath = db.get_ath(test_db)
    assert ath["price"] == pytest.approx(0.00001)
    assert ath["market_cap"] == pytest.approx(10000.0)


def test_ath_returns_none_when_not_set(test_db):
    assert db.get_ath(test_db) is None


def test_get_set_whale_state(test_db):
    db.set_whale_state(test_db, "abc123sig")
    assert db.get_whale_state(test_db) == "abc123sig"


def test_insert_volume_history(test_db):
    db.upsert_volume(test_db, date="2026-06-27", volume_usd=5000.0)
    avg = db.get_average_volume(test_db, lookback_days=7)
    assert avg == pytest.approx(5000.0)
