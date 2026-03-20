"""SQLite-backed chat session history for the Notes Retrieval / Research agents.

All data stays local — no AWS credentials needed for storage.
"""
import json
import os
import sqlite3
import time
from datetime import datetime

TTL_DAYS = 90

_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "call_notes.db")
_conn = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_session_history (
                session_type  TEXT NOT NULL,
                timestamp     TEXT NOT NULL,
                title         TEXT,
                customer      TEXT DEFAULT '',
                source_filter TEXT DEFAULT '',
                history_json  TEXT,
                turn_count    INTEGER DEFAULT 0,
                expiry_ttl    INTEGER,
                PRIMARY KEY (session_type, timestamp)
            )
        """)
        _conn.commit()
    return _conn


def _ensure_table():
    """No-op for SQLite — table is created on first connection."""
    _get_conn()


def save_chat_session(
    session_type: str,
    title: str,
    conversation_history: list,
    customer: str = "",
    source_filter: str = "",
    existing_timestamp: str = None,
) -> str:
    """Persist a chat session. Returns the timestamp key."""
    conn = _get_conn()
    ts = existing_timestamp or datetime.now().isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO chat_session_history "
        "(session_type, timestamp, title, customer, source_filter, history_json, turn_count, expiry_ttl) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (session_type, ts, title[:120], customer, source_filter,
         json.dumps(conversation_history, ensure_ascii=False),
         len(conversation_history) // 2,
         int(time.time()) + (TTL_DAYS * 86400)),
    )
    conn.commit()
    return ts


def list_chat_sessions(session_type: str | None = None, limit: int = 50) -> list[dict]:
    """Return sessions sorted by timestamp descending."""
    conn = _get_conn()
    if session_type:
        rows = conn.execute(
            "SELECT * FROM chat_session_history WHERE session_type = ? ORDER BY timestamp DESC LIMIT ?",
            (session_type, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM chat_session_history ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def load_chat_session(session_type: str, timestamp: str) -> dict | None:
    """Load a single session by its primary key."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM chat_session_history WHERE session_type = ? AND timestamp = ?",
        (session_type, timestamp),
    ).fetchone()
    if row is None:
        return None
    item = dict(row)
    if "history_json" in item and item["history_json"]:
        item["conversation_history"] = json.loads(item["history_json"])
    return item


def delete_chat_session(session_type: str, timestamp: str):
    conn = _get_conn()
    conn.execute(
        "DELETE FROM chat_session_history WHERE session_type = ? AND timestamp = ?",
        (session_type, timestamp),
    )
    conn.commit()
