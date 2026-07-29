import sqlite3
import json
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "contract_history.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            uploaded_at TEXT NOT NULL,
            user_position TEXT,
            document_type TEXT,
            overall_score INTEGER,
            grade TEXT,
            summary TEXT,
            clauses_json TEXT,
            risk_flags_json TEXT,
            benchmarks_json TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_analysis(filename: str, user_position: str, result: dict, overall_score: int, grade: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO analyses
            (filename, uploaded_at, user_position, document_type, overall_score, grade,
             summary, clauses_json, risk_flags_json, benchmarks_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            filename,
            datetime.now(timezone.utc).isoformat(),
            user_position,
            result.get("document_type", ""),
            overall_score,
            grade,
            result.get("summary", ""),
            json.dumps(result.get("clauses", [])),
            json.dumps(result.get("risk_flags", [])),
            json.dumps(result.get("benchmarks", [])),
        ),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_recent_analyses(limit: int = 20) -> list:
    """Lightweight summary list — for a sidebar/history view, not the full detail."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, filename, uploaded_at, user_position, document_type, overall_score, grade
        FROM analyses
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_analysis_by_id(analysis_id: int) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    data["clauses"] = json.loads(data.pop("clauses_json"))
    data["risk_flags"] = json.loads(data.pop("risk_flags_json"))
    data["benchmarks"] = json.loads(data.pop("benchmarks_json"))
    return data