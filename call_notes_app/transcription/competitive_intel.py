"""SQLite-backed competitive intelligence tracker.

Stores competitor mentions extracted from call notes. All data stays local.
"""
import os
import sqlite3
import time
from datetime import datetime

TTL_DAYS = 365

_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "call_notes.db")
_conn = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("""
            CREATE TABLE IF NOT EXISTS competitive_intel (
                competitor TEXT NOT NULL,
                timestamp  TEXT NOT NULL,
                customer   TEXT DEFAULT '',
                context    TEXT DEFAULT '',
                sentiment  TEXT DEFAULT 'neutral',
                expiry_ttl INTEGER,
                PRIMARY KEY (competitor, timestamp)
            )
        """)
        _conn.commit()
    return _conn


def _ensure_table():
    """No-op for SQLite — table is created on first connection."""
    _get_conn()


def save_competitor_mentions(customer_name: str, mentions: list):
    """Save extracted competitor mentions locally."""
    conn = _get_conn()
    ts = datetime.now().isoformat()
    for m in mentions:
        competitor = m.get("competitor", "").strip()
        if not competitor:
            continue
        conn.execute(
            "INSERT OR REPLACE INTO competitive_intel "
            "(competitor, timestamp, customer, context, sentiment, expiry_ttl) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (competitor, ts, customer_name, m.get("context", ""),
             m.get("sentiment", "neutral"),
             int(time.time()) + (TTL_DAYS * 86400)),
        )
    conn.commit()


def get_all_mentions(limit=100) -> list:
    """Return all competitor mentions, sorted by most recent."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM competitive_intel ORDER BY timestamp DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_mentions_by_competitor(competitor: str) -> list:
    """Return all mentions of a specific competitor."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM competitive_intel WHERE competitor = ? ORDER BY timestamp DESC",
        (competitor,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_competitor_summary() -> dict:
    """Return a summary: {competitor: count} sorted by frequency."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT competitor, COUNT(*) as cnt FROM competitive_intel GROUP BY competitor ORDER BY cnt DESC"
    ).fetchall()
    return {r["competitor"]: r["cnt"] for r in rows}
