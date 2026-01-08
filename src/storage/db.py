import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Iterator
from contextlib import contextmanager

DEFAULT_DB_PATH = "data/data.db"


def ensure_dir_for_path(path: str) -> None:
    parent = Path(path).parent
    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def db_connect(path: Optional[str] = None) -> Iterator[sqlite3.Cursor]:
    if path is None:
        path = DEFAULT_DB_PATH
    ensure_dir_for_path(path)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def init_db(path: Optional[str] = None):
    if path is None:
        path = DEFAULT_DB_PATH
    with db_connect(path) as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scans(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                results_json TEXT NOT NULL,
                count INTEGER,
                status_code INTEGER,
                response_size INTEGER
            )
            """
        )


def save_scan(
    target: str,
    results_json: str,
    meta: Optional[dict] = None,
    path: Optional[str] = None,
) -> int:
    if path is None:
        path = DEFAULT_DB_PATH

    ts = datetime.now().isoformat()
    count = meta.get("count") if meta else None
    status_code = meta.get("status_code") if meta else None
    response_size = meta.get("response_size") if meta else None

    with db_connect(path) as cursor:
        cursor.execute(
            """
            INSERT INTO scans (target, timestamp, results_json, count, status_code, response_size)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (target, ts, results_json, count, status_code, response_size),
        )
        return cursor.lastrowid


def get_scan(scan_id: int, path: Optional[str] = None) -> Optional[dict]:
    if path is None:
        path = DEFAULT_DB_PATH
    with db_connect(path) as cursor:
        cursor.execute("SELECT * FROM scans WHERE id = ?", (scan_id,))
        row = cursor.fetchone()
    return dict(row) if row else None
