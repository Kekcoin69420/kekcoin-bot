import pytest
import sqlite3
import db


@pytest.fixture
def test_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = db.init_db(db_path)
    yield conn
    conn.close()
