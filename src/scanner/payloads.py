import json
from typing import List
from .types import Payload, VulnType, Severity, MatchType


def load_payloads(path: str) -> List[Payload]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

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
            print(f"Can't load payloads: {str(e)}")
            continue
    return out
