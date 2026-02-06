"""
Модуль предоставляет класс  абстракицю Payload
и вспомогательные классы и функции для удобной работы с ним

Классы:
    Payload - класс с payload и дополнительной полезной информацией
    enum:
        Severity - опасность пэйлойда
        VulnType - тип уязвимости
        MatchType - тип поля

Функции:
    load_payloads() - десереализация объектов Payload из json
"""

import json
from enum import Enum
from typing import List, Any, Dict
from dataclasses import dataclass, asdict
from src.logger import get_logger

logger = get_logger(__name__)


class Severity(Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class VulnType(Enum):
    SQLI = "SQLI"
    XSS = "XSS"


class MatchType(Enum):
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
    Класс представляет собой удобную обертку пэйлойда

    Поля:
        payload_id - id
        payload - строка пэйлойд
        vuln_type - тип угрозы
        severity - опасность
        match_type - тип атаки
        evidence_patterns - кратко, возможные причины
    """

    payload_id: str
    payload: str
    vuln_type: VulnType
    severity: Severity
    match_type: MatchType
    evidence_patterns: List[str]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["vuln_type"] = self.vuln_type.name
        d["severity"] = self.severity.name
        d["match_type"] = self.match_type.name
        return d


def load_payloads(path: str) -> List[Payload]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Т.к. в файле храниться множесто payload создаем их список
    out: List[Payload] = []
    for p in raw:
        try:
            out.append(
                Payload(
                    payload_id=p["payload_id"],
                    payload=p["payload"],
                    vuln_type=VulnType(p.get("vuln_type")),
                    severity=Severity(p.get("severity")),
                    match_type=MatchType(p.get("match_type")),
                    evidence_patterns=p.get("evidence_patterns", []),
                )
            )
        except Exception as e:
            logger.error(
                f"Problem during loading payload {p.get('payload_id')}: {str(e)}"
            )
            # не обрываем workflow
            continue
    logger.info("Loaded payloads", extra={"path": path, "count": len(out)})
    return out
