from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "app.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS routing_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                predicted_class TEXT NOT NULL,
                confidence REAL NOT NULL,
                model_used TEXT NOT NULL,
                fallback_applied INTEGER NOT NULL DEFAULT 0,
                route_reason TEXT NOT NULL DEFAULT '',
                latency_ms REAL NOT NULL,
                estimated_cost REAL NOT NULL,
                response TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        ensure_column(conn, "routing_logs", "fallback_applied", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(conn, "routing_logs", "route_reason", "TEXT NOT NULL DEFAULT ''")


def ensure_column(
    conn: sqlite3.Connection, table_name: str, column_name: str, column_sql: str
) -> None:
    columns = {
        row[1]
        for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in columns:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")


def insert_route_log(record: dict[str, Any]) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO routing_logs (
                prompt, predicted_class, confidence, model_used,
                fallback_applied, route_reason, latency_ms, estimated_cost, response
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["prompt"],
                record["predicted_class"],
                record["confidence"],
                record["model_used"],
                int(record["fallback_applied"]),
                record["route_reason"],
                record["latency_ms"],
                record["estimated_cost"],
                record["response"],
            ),
        )


def fetch_recent_logs(limit: int = 50) -> list[dict[str, Any]]:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, prompt, predicted_class, confidence, model_used,
                   fallback_applied, route_reason, latency_ms, estimated_cost,
                   response, created_at
            FROM routing_logs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def fetch_summary() -> dict[str, Any]:
    with get_connection() as conn:
        total_routes = conn.execute("SELECT COUNT(*) FROM routing_logs").fetchone()[0]
        avg_latency = conn.execute(
            "SELECT COALESCE(AVG(latency_ms), 0) FROM routing_logs"
        ).fetchone()[0]
        total_cost = conn.execute(
            "SELECT COALESCE(SUM(estimated_cost), 0) FROM routing_logs"
        ).fetchone()[0]
        fallback_routes = conn.execute(
            "SELECT COUNT(*) FROM routing_logs WHERE fallback_applied = 1"
        ).fetchone()[0]

    return {
        "total_routes": total_routes,
        "average_latency_ms": round(avg_latency or 0.0, 2),
        "total_estimated_cost": round(total_cost or 0.0, 6),
        "fallback_routes": fallback_routes,
    }
