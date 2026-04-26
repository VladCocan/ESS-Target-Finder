import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path("/data/ess_target_finder.sqlite3")

CREATE_SYSTEMS_TABLE = """
CREATE TABLE IF NOT EXISTS systems (
    system_id INTEGER PRIMARY KEY,
    system_name TEXT NOT NULL,
    security_status REAL NOT NULL,
    constellation_id INTEGER,
    constellation_name TEXT,
    region_id INTEGER,
    region_name TEXT,
    updated_at TEXT NOT NULL
)
"""


def _connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=5.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _ensure_columns(conn: sqlite3.Connection) -> None:
    rows = conn.execute("PRAGMA table_info(systems)").fetchall()
    existing = {row[1] for row in rows}
    if "constellation_name" not in existing:
        conn.execute("ALTER TABLE systems ADD COLUMN constellation_name TEXT")
    if "region_name" not in existing:
        conn.execute("ALTER TABLE systems ADD COLUMN region_name TEXT")


def init_db() -> None:
    with _connection() as conn:
        conn.execute(CREATE_SYSTEMS_TABLE)
        _ensure_columns(conn)
        conn.commit()


def get_system_count() -> int:
    with _connection() as conn:
        row = conn.execute("SELECT COUNT(*) FROM systems").fetchone()
    return int(row[0]) if row else 0


def get_system_metadata(system_id: int) -> Optional[dict[str, Any]]:
    if system_id <= 0:
        return None

    with _connection() as conn:
        row = conn.execute(
            "SELECT system_id, system_name, security_status, constellation_id, constellation_name, region_id, region_name, updated_at FROM systems WHERE system_id = ?",
            (system_id,),
        ).fetchone()

    if not row:
        return None

    return {
        "system_id": row[0],
        "system_name": row[1],
        "security_status": float(row[2]),
        "constellation_id": row[3],
        "constellation_name": row[4],
        "region_id": row[5],
        "region_name": row[6],
        "updated_at": row[7],
    }


def upsert_system_metadata(
    system_id: int,
    system_name: str,
    security_status: float,
    constellation_id: int | None,
    constellation_name: str | None,
    region_id: int | None,
    region_name: str | None,
) -> None:
    if system_id <= 0:
        return

    now = datetime.utcnow().isoformat()
    with _connection() as conn:
        conn.execute(
            """
            INSERT INTO systems (
                system_id,
                system_name,
                security_status,
                constellation_id,
                constellation_name,
                region_id,
                region_name,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(system_id) DO UPDATE SET
                system_name = excluded.system_name,
                security_status = excluded.security_status,
                constellation_id = excluded.constellation_id,
                constellation_name = excluded.constellation_name,
                region_id = excluded.region_id,
                region_name = excluded.region_name,
                updated_at = excluded.updated_at
            """,
            (
                system_id,
                system_name,
                security_status,
                constellation_id,
                constellation_name,
                region_id,
                region_name,
                now,
            ),
        )
        conn.commit()


def get_security_status(system_id: int) -> Optional[float]:
    if system_id <= 0:
        return None

    with _connection() as conn:
        row = conn.execute(
            "SELECT security_status FROM systems WHERE system_id = ?",
            (system_id,),
        ).fetchone()

    if not row:
        return None

    return float(row[0])
