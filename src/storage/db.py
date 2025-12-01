import sqlite3
import json
from datetime import datetime
from typing import Optional

DEFAULT_DB_PATH = "data.db"


def use_db(func):
    def wrapper(path: str = DEFAULT_DB_PATH, *args, **kwargs):
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row
        try:
            result = func(cursor, *args, **kwargs)
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            print(f"Database error: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    return wrapper


@use_db
def init_db(cursor):
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


@use_db
def save_scan(cursor, target: str, results_json: str, meta: dict = None) -> int:
    timestamp = datetime.now()
    count = meta.get("count") if meta else None
    status_code = meta.get("status_code") if meta else None
    response_size = meta.get("response_size") if meta else None
    cursor.execute(
        """
        INSERT INTO scans (target, timestamp, results_json, count, status_code, response_size)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (target, timestamp, results_json, count, status_code, response_size),
    )
    return cursor.lastrowid


@use_db
def get_scan(cursor, scan_id: int) -> Optional[dict]:
    cursor.execute("SELECT * FROM scans WHERE id = ?", (scan_id,))
    row = cursor.fetchone()
    if row:
        return {k: row[k] for k in row.keys()}
    else:
        return None
