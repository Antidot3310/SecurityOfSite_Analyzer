"""
Модуль предоставляет детекторы различных видов уязвимостей,
их работа основана на сравнении базового запроса с инжектированным

Фукнции:
    run_detectors() - запускает все детекторы ниже
    detect_time_delay() - определяет большую разницу задержек запросов
    detect_sql_error() - находит ошибки sql  в ответе
    detect_patterns() - определяет следы xss
"""

import json, html, urllib.parse, re
from typing import List, Dict
from pathlib import Path
from .types import Payload
from src.logger import get_logger

logger = get_logger(__name__)

SQL_ERRORS_PATH = Path(__file__).parent.parent.parent / "data" / "sql_errors.json"
try:
    SQL_ERROR_LIST = [
        s.lower() for s in json.loads(SQL_ERRORS_PATH.read_text(encoding="utf-8"))
    ]
except Exception:
    SQL_ERROR_LIST = []


def detect_patterns(base, injected, payload: Payload) -> Dict:
    """
    определяет наличие следов payload в отввете сервера
    """
    base_text = (base.body or "").lower()
    inj_text = (injected.body or "").lower()

    patterns = []
    patterns.extend(payload.evidence_patterns or [])

    # Добавляем варианты payload
    # (оригинальную версию, html-экранированную, url кодированную и без пробелов)
    raw = (payload.payload or "").lower()
    if raw:
        patterns.extend(
            {
                raw,
                html.escape(raw),
                urllib.parse.quote(raw),
                re.sub(r"\s+", "", raw),
            }
        )
    # Логируем кандидатов
    logger.debug(
        "reflection candidate",
        extra={"payload": raw, "patterns": patterns},
    )
    # находим паттерн и возвращаем контекст
    for p in patterns:
        p = p.lower()
        if p and p in inj_text and p not in base_text:
            pos = inj_text.find(p)
            start = max(0, pos - 30)
            end = pos + len(p) + 30
            return {
                "matched": True,
                "evidence": (injected.body or "")[start:end],
            }

    return {"matched": False, "evidence": ""}


def detect_sql_error(base, injected, payload: Payload) -> Dict:
    """
    Определяет наличие ошибок sql в тестовом запросе
    при их отсутствии в базовом запросе"""
    b = (base.body or "").lower()
    i = (injected.body or "").lower()
    for err in SQL_ERROR_LIST:
        if err and err in i and err not in b:
            return {"matched": True, "evidence": err}
    return {"matched": False, "evidence": ""}


def detect_time_delay(base, injected, payload: Payload) -> Dict:
    """
    Отмечает наличие пороговой задержки
    """
    threshold_ms = 2000
    if (injected.response_time - base.response_time) > threshold_ms:
        return {
            "matched": True,
            "evidence": f"time delay: {injected.response_time - base.response_time:.0f} ms",
        }
    return {"matched": False, "evidence": ""}


DETECTORS = (detect_sql_error, detect_patterns, detect_time_delay)


def run_detectors(base, injected, payload: Payload) -> List[Dict]:
    """
    Запускает все детекторы на тестовый и базовый запрос
    """
    result = []
    for detect in DETECTORS:
        try:
            res = detect(base, injected, payload)
            if res and res.get("matched"):
                result.append(res)
                logger.info(
                    "detector matched",
                    extra={
                        "detector": detect.__name__,
                        "payload_id": payload.payload_id,
                        "evidence_preview": res.get("evidence", "")[:100],
                    },
                )
        except Exception as e:
            logger.exception("Problem during detecting", extra={"error": str(e)})
            continue
    return result
