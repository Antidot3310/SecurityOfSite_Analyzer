import sqlite3
from datetime import datetime
from typing import Optional, Iterator, Any
from contextlib import contextmanager

DEFAULT_DB_PATH = "data/data.db"


@contextmanager
def db_connect(path: str = DEFAULT_DB_PATH) -> Iterator[sqlite3.Cursor]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise sqlite3.Error(f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()


def init_db(path: str = DEFAULT_DB_PATH):
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
    path: str = DEFAULT_DB_PATH,
) -> int:
    with db_connect(path) as cursor:
        cursor.execute(
            """
                INSERT INTO scans (target, timestamp, results_json, count, status_code, response_size)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                target,
                datetime.now(),
                results_json,
                meta.get("count"),
                meta.get("status_code"),
                meta.get("response_size"),
            ),
        )
    return cursor.lastrowid


def get_scan(scan_id: int, path: str = DEFAULT_DB_PATH) -> Optional[dict]:
    with db_connect(path) as cursor:
        cursor.execute("SELECT * FROM scans WHERE id = ?", (scan_id,))
        row = cursor.fetchone()
    return dict(row) if row else None
