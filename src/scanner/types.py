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
