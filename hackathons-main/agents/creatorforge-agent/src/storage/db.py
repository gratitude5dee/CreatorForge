"""SQLite connection and migration management."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path


class Database:
    """Thread-safe SQLite helper."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = threading.Lock()
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        migration_dir = Path(__file__).resolve().parent / "migrations"
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS _migrations (
                      name TEXT PRIMARY KEY,
                      applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                applied = {
                    row["name"]
                    for row in conn.execute("SELECT name FROM _migrations").fetchall()
                }
                for migration in sorted(migration_dir.glob("*.sql")):
                    if migration.name in applied:
                        continue
                    conn.executescript(migration.read_text(encoding="utf-8"))
                    conn.execute(
                        "INSERT INTO _migrations (name) VALUES (?)",
                        (migration.name,),
                    )
                conn.commit()

    def execute(self, sql: str, params: tuple = ()) -> int:
        with self._lock:
            with self._connect() as conn:
                cur = conn.execute(sql, params)
                conn.commit()
                return int(cur.lastrowid)

    def fetchone(self, sql: str, params: tuple = ()) -> dict | None:
        with self._lock:
            with self._connect() as conn:
                row = conn.execute(sql, params).fetchone()
                return dict(row) if row else None

    def fetchall(self, sql: str, params: tuple = ()) -> list[dict]:
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(sql, params).fetchall()
                return [dict(r) for r in rows]
