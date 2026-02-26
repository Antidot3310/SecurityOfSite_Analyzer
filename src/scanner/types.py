"""
Модуль предоставляет класс Payload (абстракция полезной нагрузки)

Классы:
    Payload   – полезная нагрузка с метаинформацией.
    Severity  – уровень опасности.
    VulnType  – тип уязвимости.
    MatchType – способ срабатывания.

Функции:
    load_payloads() – десериализация списка Payload из JSON-файла.
"""

import json
from enum import Enum
from typing import List, Any, Dict
from dataclasses import dataclass, asdict
from src.logger import get_logger

logger = get_logger(__name__)


class Severity(Enum):
    """Уровень опасности уязвимости."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class VulnType(Enum):
    """Тип уязвимости."""

    SQLI = "SQLI"
    XSS = "XSS"


class MatchType(Enum):
    """Способ срабатывания детектора."""

    BOOLEAN = "BOOLEAN"
    UNION = "UNION"
    TIME_BASED = "TIME_BASED"
    REFLECTED = "REFLECTED"
    STORED = "STORED"
    DOM_BASED = "DOM_BASED"
    POLYGLOT = "POLYGLOT"
    ERROR_BASED = "ERROR_BASED"


@dataclass
class Payload:
    """
    Полезная нагрузка с метаданными.

    Атрибуты:
        payload_id: уникальный идентификатор.
        payload: строка, внедряемая в поле формы.
        vuln_type: тип уязвимости (из VulnType).
        severity: уровень опасности (из Severity).
        match_type: способ срабатывания (из MatchType).
        evidence_patterns: список паттернов, подтверждающих уязвимость.
    """

    payload_id: str
    payload: str
    vuln_type: VulnType
    severity: Severity
    match_type: MatchType
    evidence_patterns: List[str]

    def to_dict(self) -> dict:
        return {
            "payload_id": self.payload_id,
            "payload": self.payload,
            "vuln_type": self.vuln_type.name,
            "severity": self.severity.name,
            "match_type": self.match_type.name,
            "evidence_patterns": self.evidence_patterns,
        }


def load_payloads(path: str) -> List[Payload]:
    """
    Загружает список полезных нагрузок из JSON-файла.

    Параметры:
        path: путь к JSON-файлу.

    Формат файла: список объектов Payload.
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, list):
        logger.error(f"Expected list of payloads in {path}, got {type(raw).__name__}")
        return []

    out: List[Payload] = []
    for item in raw:
        try:
            payload = Payload(
                payload_id=item["payload_id"],
                payload=item["payload"],
                vuln_type=VulnType(item["vuln_type"]),
                severity=Severity(item["severity"]),
                match_type=MatchType(item["match_type"]),
                evidence_patterns=item.get("evidence_patterns", []),
            )
            out.append(payload)
        except (ValueError, KeyError, TypeError) as e:
            logger.error(
                "Failed to parse payload",
                extra={"payload_id": item.get("payload_id"), "error": str(e)},
            )
            continue

    logger.info("Payloads loaded", extra={"path": path, "count": len(out)})
    return out
