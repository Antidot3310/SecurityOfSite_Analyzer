import json
from typing import List
from .types import VulnType, Severity, MatchType, Payload


def load_payloads(path: str) -> List[Payload]:
    with open(path, "r", encoding="UTF-8") as file:
        raw = json.load(file)
    payloads = []
    for p in raw:
        payloads.append(
            Payload(
                payload_id=p["payload_id"],
                payload=p["payload"],
                vuln_type=VulnType(p["vuln_type"]),
                severity=Severity(p["severity"]),
                match_type=MatchType(p["match_type"]),
                evidence_patterns=p["evidence_patterns"],
            )
        )
    return payloads
