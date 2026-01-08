from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Any, Dict

class Severity(Enum):
    INFO = "Info"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class VulnType(Enum):
    SQLI = "SQL Injection"
    XSS = "Cross-Site Scripting"
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


@dataclass
class Payload:
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
