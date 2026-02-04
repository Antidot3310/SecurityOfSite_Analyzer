"""
Модуль для настройки и получения логгеров.
"""

import json
import logging
import os
from src.config import LOG_LEVEL


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
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
}


class ExtraFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # собрать дополнительные поля (которые добавлены через extra)
        extras = {}
        for k, v in record.__dict__.items():
            if k not in _STANDARD_ATTRS:
                # не включаем внутренние объекты логгера
                if k in ("args", "msg"):
                    continue
                extras[k] = v

        # создаём компактный repr: первые 200 символов для больших значений
        compact = {}
        for k, v in extras.items():
            try:
                s = json.dumps(v, default=str)
            except Exception:
                s = str(v)
            compact[k] = s if len(s) <= 200 else s[:200] + "...(truncated)"

        # добавляем поле `context` в record, чтобы форматтер мог его использовать
        record.context = json.dumps(compact, ensure_ascii=False) if compact else ""
        return super().format(record)


def configure_basic_logging():
    root = logging.getLogger()

    level = getattr(logging, LOG_LEVEL, logging.DEBUG)
    root.setLevel(level)

    fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s %(context)s"

    # Если есть существующие хендлеры — обновим их форматтер и уровень.
    if root.handlers:
        for h in root.handlers:
            try:
                h.setLevel(level)
                h.setFormatter(ExtraFormatter(fmt))
            except Exception:
                # не фейлим если какой-то хендлер особенный
                try:
                    h.setFormatter(logging.Formatter(fmt))
                except Exception:
                    pass
        return

    # Нет хендлеров — создаём свой.
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(ExtraFormatter(fmt))
    root.addHandler(ch)


def get_logger(name: str):
    configure_basic_logging()
    return logging.getLogger(name)
