from .scanner import ResponseSnapshot, Payload
from typing import List
from pathlib import Path
import json
import html
import urllib.parse
import re

p = Path(__file__).parent / "sql_errors.json"
try:
    with open("sql_errors.json", "r", encoding="UTF-8") as f:
        SQL_ERROR_LIST = json.load(f)
except Exception as e:
    print(f"Error within loading sql_errors.json: {str(e)}")
    SQL_ERROR_LIST = []


class DetectedResult:
    def __init__(self, matched: bool, evidence: str):
        self.matched = matched
        self.evidence = evidence

    def to_dict(self):
        return {
            "matched": self.matched,
            "evidence": self.evidence,
        }


def detect_reflection(base, injected, payload):
    base_lower = (base.body or "").lower()
    inj_lower = (injected.body or "").lower()

    if "alert(" in payload.payload.lower():
        search_for = "alert(1)"
    else:
        search_for = re.sub(r"[^a-zA-Z0-9]", "", payload.payload)[:8]
        if len(search_for) < 4:
            return {"matched": False, "evidence": "", "confidence": 0}

    variants = {search_for, html.escape(search_for), urllib.parse.quote(search_for)}

    for variant in variants:
        if variant in inj_lower and variant not in base_lower:
            pos = (injected.body or "").lower().find(variant)
            if pos != -1:
                start = max(0, pos - 30)
                end = pos + len(variant) + 30
                evidence = (injected.body or "")[start:end]
                return {
                    "matched": True,
                    "evidence": evidence,
                }

    return {"matched": False, "evidence": ""}


def detect_sql_error(
    base: ResponseSnapshot, injected: ResponseSnapshot, payload: Payload
) -> dict:
    for err in SQL_ERROR_LIST:
        if err in injected.body.lower() and not err in base.body.lower():
            return DetectedResult(
                matched=True, evidence=payload.evidence_patterns
            ).to_dict()
    return {"matched": False, "evidence": ""}


def detect_time_delay(
    base: ResponseSnapshot, injected: ResponseSnapshot, payload: Payload
) -> dict:
    threshold_ms = 2000  # ms
    if injected.response_time - base.response_time > threshold_ms:
        return {
            "matched": True,
            "evidence": f"Time delay detected: {injected.response_time - base.response_time} ms",
        }
    return {"matched": False, "evidence": ""}


def run_detectors(
    base: ResponseSnapshot, injected: ResponseSnapshot, payload: Payload
) -> List[dict]:
    detectors = [detect_sql_error, detect_reflection, detect_time_delay]
    det_res = []
    for detector in detectors:
        dr = detector(base, injected, payload)
        if dr and dr["matched"]:
            det_res.append(dr)
    return det_res
