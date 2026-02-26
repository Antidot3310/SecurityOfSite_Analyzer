"""
Минималистичный логгер:
Выводит: время, уровень, модуль, сообщение и дополнительные поля (extra).
Сделан упор на читаемость (выравнивание) и простоту использования.
"""

import json
import logging
from typing import Dict, Any
from src.config import LOG_LEVEL

# Небольшой набор стандартных атрибутов LogRecord, которые не считаем extra.
_STANDARD_ATTRS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "threadName",
    "processName",
    "process",
    "message",
    "exc_text",
    "thread",
    "taskName",
}
_MAX_EXTRA_VAL = 200


class SimpleFormatter(logging.Formatter):
    """
    Форматирует запись в виде:
    2026-02-18 19:14:51 INFO  [module.name] message ... | key = value | other = value2

    - module name выравнивается по ширине.
    - extra поля сериализуются в JSON-подобный вид.
    """

    def __init__(self):
        fmt = (
            "%(asctime)s %(levelname)-5s [%(name)-"
            + "s] %(message)s%(context_suffix)s"
        )
        datefmt = "%H:%M:%S"
        super().__init__(fmt=fmt, datefmt=datefmt)

    def format(self, record: logging.LogRecord) -> str:
        extras: Dict[str, Any] = {
            k: v for k, v in record.__dict__.items() if k not in _STANDARD_ATTRS
        }

        if extras:
            maxk = max(len(k) for k in extras.keys())
            parts = []
            for k, v in extras.items():
                try:
                    s = json.dumps(v, ensure_ascii=False)
                except Exception:
                    s = str(v)
                if len(s) > _MAX_EXTRA_VAL:
                    s = s[:_MAX_EXTRA_VAL] + "...(truncated)"
                parts.append(f"{k.ljust(maxk)} = {s}")
            record.context_suffix = " | " + " | ".join(parts)
        else:
            record.context_suffix = ""

        return super().format(record)


def configure_basic_logging():
    """
    Инициализация логгера — idempotent: можно вызывать несколько раз без дублирования хендлеров.
    """
    root = logging.getLogger()

    root.setLevel(LOG_LEVEL)

    if root.handlers:
        root.handlers = []

    fmt = SimpleFormatter()

    ch = logging.StreamHandler()
    ch.setLevel(LOG_LEVEL)
    ch.setFormatter(fmt)
    root.addHandler(ch)


def get_logger(name: str) -> logging.Logger:
    """
    Получить логгер по имени; гарантированно настроит базовую конфигурацию при первом вызове.
    """
    configure_basic_logging()
    return logging.getLogger(name)
