"""
Модуль предоставляет детекторы различных видов уязвимостей.
Каждый детектор сравнивает базовый ответ с инжектированным.

Функции:
    run_detectors() - запускает все детекторы и возвращает список сработавших.
    detect_time_delay() - обнаруживает аномальную задержку ответа.
    detect_sql_error() - ищет признаки SQL-ошибок в теле ответа.
    detect_patterns() - ищет отражение полезной нагрузки (XSS).
"""

import re
import html
import urllib.parse
import json
from typing import List, Dict, Set

from .types import Payload
from .models import ResponseSnapshot
from src.config import TIME_DELAY_THRESHOLD_MS, SQL_ERRORS_PATH
from src.logger import get_logger

logger = get_logger(__name__)

DEFAULT_CONTEXT_SIZE = 60
try:
    with open(SQL_ERRORS_PATH, "r", encoding="utf-8") as f:
        SQL_ERROR_LIST = [s.lower() for s in json.load(f)]
    logger.debug(f"Loaded {len(SQL_ERROR_LIST)} SQL error signatures")
except Exception as e:
    logger.exception(f"Failed to load SQL errors from {SQL_ERRORS_PATH}")


def generate_payload_variants(payload: str) -> Set[str]:
    """Возвращает набор вариантов payload для поиска отражения."""
    variants = {payload}
    try:
        variants.add(html.escape(payload))
        variants.add(urllib.parse.quote_plus(payload))
    except Exception:
        pass
    variants.add(re.sub(r"\s+", "", payload))
    variants.add(re.sub(r"\W+", "", payload))
    variants.discard("")
    return variants


def extract_context(
    text: str, substring: str, context_size: int = DEFAULT_CONTEXT_SIZE
) -> str:
    """Возвращает фрагмент текста вокруг найденного substring."""
    if not text or not substring:
        return ""
    idx = text.find(substring)
    if idx == -1:
        return ""
    start = max(0, idx - context_size)
    end = min(idx + len(substring) + context_size, len(text))
    return text[start:end]


def detect_patterns(
    base: ResponseSnapshot, injected: ResponseSnapshot, payload: Payload
) -> Dict:
    """Ищет отражение полезной нагрузки в ответе."""
    base_body = base.body or ""
    inj_body = injected.body or ""

    variants = generate_payload_variants(payload.payload)

    for variant in variants:
        if variant and variant in inj_body and variant not in base_body:
            return {
                "matched": True,
                "evidence": extract_context(inj_body, variant),
            }

    return {"matched": False, "evidence": ""}


def detect_sql_error(
    base: ResponseSnapshot, injected: ResponseSnapshot, payload: Payload
) -> Dict:
    """Ищет признаки SQL-ошибок в injected-ответе, которых нет в base."""
    base_body = base.body or ""
    inj_body = injected.body or ""

    for signature in SQL_ERROR_LIST:
        match_inj = re.search(signature, inj_body, flags=re.IGNORECASE)
        if match_inj and not re.search(signature, base_body, flags=re.IGNORECASE):
            start = max(match_inj.start() - 200, 0)
            end = min(match_inj.end() + 200, len(inj_body))
            return {
                "matched": True,
                "evidence": inj_body[start:end],
            }

    return {"matched": False, "evidence": ""}


def detect_time_delay(
    base: ResponseSnapshot, injected: ResponseSnapshot, payload: Payload
) -> Dict:
    """Сравнивает время ответа базового и инжектированного запросов."""
    delay = injected.response_time - base.response_time
    if delay > TIME_DELAY_THRESHOLD_MS:
        return {"matched": True, "evidence": f"Time delay: {delay:.0f} ms"}
    return {"matched": False, "evidence": ""}


DETECTORS = (detect_sql_error, detect_patterns, detect_time_delay)


def run_detectors(
    base: ResponseSnapshot, injected: ResponseSnapshot, payload: Payload
) -> List[Dict]:
    """Запускает все детекторы и возвращает список сработавших."""
    findings = []
    for detector in DETECTORS:
        try:
            finding = detector(base, injected, payload)
            if finding and finding.get("matched"):
                findings.append(finding)
        except Exception as e:
            logger.exception(
                "Error in detector",
                extra={
                    "detector": detector.__name__,
                    "payload_id": payload.payload_id,
                    "error": str(e),
                },
            )
    return findings
