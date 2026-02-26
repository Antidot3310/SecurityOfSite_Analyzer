"""
Модуль предоставляет детекторы различных видов уязвимостей.
Каждый детектор сравнивает базовый ответcс инжектированным

Функции:
    run_detectors() - запускает все детекторы и возвращает список сработавших.
    detect_time_delay() - обнаруживает аномальную задержку ответа.
    detect_sql_error() - ищет признаки SQL-ошибок в теле ответа.
    detect_patterns() - ищет отражение полезной нагрузки (XSS).
"""

import json
import html
import urllib.parse
import re
from typing import List, Dict

from .types import Payload
from .models import ResponseSnapshot
from src.config import SQL_ERRORS_PATH, TIME_DELAY_THRESHOLD_MS
from src.logger import get_logger

logger = get_logger(__name__)

SQL_ERROR_LIST: List[str] = []
try:
    with open(SQL_ERRORS_PATH, "r", encoding="utf-8") as f:
        SQL_ERROR_LIST = [s.lower() for s in json.load(f)]
    logger.debug(f"Loaded {len(SQL_ERROR_LIST)} SQL error signatures")
except Exception as e:
    logger.exception(f"Failed to load SQL errors from {SQL_ERRORS_PATH}")


def detect_patterns(
    base: ResponseSnapshot, injected: ResponseSnapshot, payload: Payload
) -> Dict:
    """
    Определяет наличие отражённой полезной нагрузки в ответе сервера.

    Возвращает словарь с ключами:
        'matched': bool,
        'evidence': фрагмент ответа, содержащий найденный паттерн.
    """
    base_body = (base.body or "").lower()
    inj_body = (injected.body or "").lower()
    base_lower = base_body.lower()
    inj_lower = inj_body.lower()

    patterns = set()
    if payload.evidence_patterns:
        patterns.update(p.lower() for p in payload.evidence_patterns)

    raw_payload = (payload.payload or "").lower()
    if raw_payload:
        patterns.update(
            [
                raw_payload,
                html.escape(raw_payload),
                urllib.parse.quote(raw_payload),
                re.sub(r"\s+", "", raw_payload),
            ]
        )

    patterns.discard("")

    logger.debug(
        "Reflection search",
        extra={
            "payload_id": payload.payload_id,
            "patterns_count": len(patterns),
        },
    )

    for pattern in patterns:
        if pattern in inj_lower and pattern not in base_lower:
            pos = inj_lower.find(pattern)
            if pos != -1:
                start = max(0, pos - 30)
                end = min(len(inj_body), pos + len(pattern) + 30)
                evidence = inj_body[start:end]
                return {"matched": True, "evidence": evidence}

    return {"matched": False, "evidence": ""}


def detect_sql_error(
    base: ResponseSnapshot, injected: ResponseSnapshot, payload: Payload
) -> Dict:
    """
    Ищет признаки SQL-ошибок в теле инжектированного ответа,
    отсутствующие в базовом.
    """
    base_body = (base.body or "").lower()
    inj_body = (injected.body or "").lower()

    for err in SQL_ERROR_LIST:
        if err and err in inj_body and err not in base_body:
            return {"matched": True, "evidence": err}

    return {"matched": False, "evidence": ""}


def detect_time_delay(
    base: ResponseSnapshot, injected: ResponseSnapshot, payload: Payload
) -> Dict:
    """
    Сравнивает время ответа базового и инжектированного запросов.
    Если разница превышает threshold_ms, считает уязвимостью.
    """
    delay_ms = injected.response_time - base.response_time
    if delay_ms > TIME_DELAY_THRESHOLD_MS:
        return {
            "matched": True,
            "evidence": f"Time delay: {delay_ms:.0f} ms",
        }
    return {"matched": False, "evidence": ""}


DETECTORS = (detect_sql_error, detect_patterns, detect_time_delay)


def run_detectors(
    base: ResponseSnapshot, injected: ResponseSnapshot, payload: Payload
) -> List[Dict]:
    """
    Запускает все зарегистрированные детекторы для пары ответов.
    Возвращает список словарей от детекторов, которые вернули matched=True.
    """
    results = []
    for detector_func in DETECTORS:
        try:
            res = detector_func(base, injected, payload)
            if res and res.get("matched"):
                results.append(res)
                logger.info(
                    "Detector matched",
                    extra={
                        "detector": detector_func.__name__,
                        "payload_id": payload.payload_id,
                        "evidence_preview": (res.get("evidence") or "")[:100],
                    },
                )
        except Exception as e:
            logger.exception(
                "Error in detector",
                extra={
                    "detector": detector_func.__name__,
                    "payload_id": payload.payload_id,
                    "error": str(e),
                },
            )
    return results
