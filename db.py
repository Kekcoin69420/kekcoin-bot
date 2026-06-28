import sqlite3
import os
from datetime import datetime, timezone, timedelta
from config import DEFAULT_FUD_KEYWORDS


def init_db(path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _create_tables(conn)
    _seed_defaults(conn)
    return conn


def _create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS praise (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        count INTEGER DEFAULT 0,
        updated_at TEXT
    );
    INSERT OR IGNORE INTO praise (id, count) VALUES (1, 0);

    CREATE TABLE IF NOT EXISTS ath (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        price REAL,
        market_cap REAL,
        recorded_at TEXT
    );

    CREATE TABLE IF NOT EXISTS fud_keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT UNIQUE COLLATE NOCASE,
        added_by INTEGER,
        added_at TEXT
    );

    CREATE TABLE IF NOT EXISTS strikes (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        count INTEGER DEFAULT 0,
        last_strike_at TEXT
    );

    CREATE TABLE IF NOT EXISTS whale_state (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        last_signature TEXT,
        updated_at TEXT
    );
    INSERT OR IGNORE INTO whale_state (id) VALUES (1);

    CREATE TABLE IF NOT EXISTS volume_history (
        date TEXT PRIMARY KEY,
        volume_usd REAL,
        recorded_at TEXT
    );

    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)
    conn.commit()


def _seed_defaults(conn: sqlite3.Connection) -> None:
    defaults = {
        "whale_threshold_usd": "500",
        "holder_milestones": "1000,5000,10000,25000,50000,100000",
        "digest_hour_utc": "9",
        "strike_mute_threshold": "3",
        "volume_spike_multiple": "2.0",
        "volume_lookback_days": "7",
    }
    for key, value in defaults.items():
        conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))
    for kw in DEFAULT_FUD_KEYWORDS:
        conn.execute("INSERT OR IGNORE INTO fud_keywords (keyword, added_by, added_at) VALUES (?, 0, ?)",
                     (kw, _now()))
    conn.commit()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- Praise ---
def get_praise(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT count FROM praise WHERE id=1").fetchone()["count"]


def increment_praise(conn: sqlite3.Connection) -> int:
    conn.execute("UPDATE praise SET count=count+1, updated_at=? WHERE id=1", (_now(),))
    conn.commit()
    return get_praise(conn)


# --- Settings ---
def get_setting(conn: sqlite3.Connection, key: str, default: str = "") -> str:
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()


# --- FUD keywords ---
def add_fud_keyword(conn: sqlite3.Connection, keyword: str, added_by: int) -> None:
    conn.execute("INSERT OR IGNORE INTO fud_keywords (keyword, added_by, added_at) VALUES (?, ?, ?)",
                 (keyword.lower(), added_by, _now()))
    conn.commit()


def remove_fud_keyword(conn: sqlite3.Connection, keyword: str) -> None:
    conn.execute("DELETE FROM fud_keywords WHERE keyword=?", (keyword.lower(),))
    conn.commit()


def list_fud_keywords(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT keyword FROM fud_keywords ORDER BY keyword").fetchall()
    return [r["keyword"] for r in rows]


# --- Strikes ---
def add_strike(conn: sqlite3.Connection, user_id: int, username: str) -> int:
    conn.execute("""
        INSERT INTO strikes (user_id, username, count, last_strike_at) VALUES (?, ?, 1, ?)
        ON CONFLICT(user_id) DO UPDATE SET count=count+1, username=excluded.username, last_strike_at=excluded.last_strike_at
    """, (user_id, username, _now()))
    conn.commit()
    return get_strike_count(conn, user_id)


def get_strike_count(conn: sqlite3.Connection, user_id: int) -> int:
    row = conn.execute("SELECT count, last_strike_at FROM strikes WHERE user_id=?", (user_id,)).fetchone()
    if not row:
        return 0
    last = datetime.fromisoformat(row["last_strike_at"])
    if datetime.now(timezone.utc) - last > timedelta(days=7):
        conn.execute("UPDATE strikes SET count=1, last_strike_at=? WHERE user_id=?", (_now(), user_id))
        conn.commit()
        return 1
    return row["count"]


def reset_strikes(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute("DELETE FROM strikes WHERE user_id=?", (user_id,))
    conn.commit()


# --- ATH ---
def get_ath(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute("SELECT price, market_cap, recorded_at FROM ath WHERE id=1").fetchone()
    return dict(row) if row else None


def set_ath(conn: sqlite3.Connection, price: float, market_cap: float) -> None:
    conn.execute("""
        INSERT INTO ath (id, price, market_cap, recorded_at) VALUES (1, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET price=excluded.price, market_cap=excluded.market_cap, recorded_at=excluded.recorded_at
    """, (price, market_cap, _now()))
    conn.commit()


# --- Whale state ---
def get_whale_state(conn: sqlite3.Connection) -> str | None:
    row = conn.execute("SELECT last_signature FROM whale_state WHERE id=1").fetchone()
    return row["last_signature"] if row else None


def set_whale_state(conn: sqlite3.Connection, signature: str) -> None:
    conn.execute("UPDATE whale_state SET last_signature=?, updated_at=? WHERE id=1", (signature, _now()))
    conn.commit()


# --- Volume history ---
def upsert_volume(conn: sqlite3.Connection, date: str, volume_usd: float) -> None:
    conn.execute("""
        INSERT INTO volume_history (date, volume_usd, recorded_at) VALUES (?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET volume_usd=excluded.volume_usd
    """, (date, volume_usd, _now()))
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    conn.execute("DELETE FROM volume_history WHERE date < ?", (cutoff,))
    conn.commit()


def get_average_volume(conn: sqlite3.Connection, lookback_days: int = 7) -> float:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    row = conn.execute("SELECT AVG(volume_usd) as avg FROM volume_history WHERE date >= ?", (cutoff,)).fetchone()
    return row["avg"] or 0.0
