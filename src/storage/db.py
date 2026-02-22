"""
Модуль для сохранения результатов сканирования веб-форм в базу данных SQLite.

Таблица `scans` содержит следующие поля:
    id              - уникальный идентификатор записи
    target          - URL или путь к ресурсу
    timestamp       - время сохранения в формате ISO
    results_json    - полные результаты анализа в JSON
    count           - количество находок
    status_code     - статус ответа
    response_size   - размер ответа в символах
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Iterator, Dict, Any
from contextlib import contextmanager
from src.config import DEFAULT_DB_PATH
from src.logger import get_logger

logger = get_logger(__name__)


def ensure_dir_for_path(path: str) -> None:
    """Создаёт родительскую директорию для файла, если её нет."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def db_connect(path: Optional[str] = None) -> Iterator[sqlite3.Cursor]:
    """
    Контекстный менеджер для подключения к БД.

    При выходе из контекста автоматически выполняет commit,
    при исключении – rollback. Возвращает курсор с row_factory = sqlite3.Row.

    Параметры:
        path: путь к файлу БД.

    Возвращает:
        Курсор для выполнения SQL-запросов.

    Исключения:
        Пробрасывает исключения БД после отката транзакции.
    """
    if path is None:
        path = DEFAULT_DB_PATH
    ensure_dir_for_path(path)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        logger.exception("DB transaction failed", extra={"path": path, "error": str(e)})
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def init_db(path: Optional[str] = None):
    """
    Создаёт таблицу scans, если она ещё не существует.

    Параметры:
        path: путь к БД (если None, используется DEFAULT_DB_PATH).
    """
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
        logger.info("Database initialized", extra={"path": path})


def save_scan(
    target: str,
    results_json: str,
    meta: Optional[Dict[str, Any]] = None,
    path: Optional[str] = None,
) -> int | None:
    """
    Сохраняет результаты сканирования в БД.

    Параметры:
        target: URL или путь к ресурсу.
        results_json: JSON-строка с детальными результатами анализа.
        meta: словарь с мета-информацией. Может содержать ключи:
              count (int) – количество найденных форм,
              status_code (int) – HTTP-статус ответа,
              response_size (int) – размер ответа в символах.
        path: путь к БД (если None, используется DEFAULT_DB_PATH).

    Возвращает:
        ID созданной записи (primary key).

    Исключения:
        Пробрасывает исключения БД при ошибках вставки.
    """

    ts = datetime.now().isoformat()
    if meta:
        count = meta.get("count")
        status_code = meta.get("status_code")
        response_size = meta.get("response_size")
    else:
        count = None
        status_code = None
        response_size = None

    with db_connect(path) as cursor:
        cursor.execute(
            """
            INSERT INTO scans (target, timestamp, results_json, count, status_code, response_size)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (target, ts, results_json, count, status_code, response_size),
        )
        scan_id = cursor.lastrowid
        logger.info("scan saved", extra={"target": target, "scan_id": scan_id})
        return scan_id


def get_scan(scan_id: int, path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Получает запись скана по её ID.

    Параметры:
        scan_id: идентификатор записи.
        path: путь к БД (если None, используется DEFAULT_DB_PATH).

    Возвращает:
        Словарь с данными записи или None, если запись не найдена.
    """
    with db_connect(path) as cursor:
        cursor.execute("SELECT * FROM scans WHERE id = ?", (scan_id,))
        row = cursor.fetchone()
    return dict(row) if row else None
