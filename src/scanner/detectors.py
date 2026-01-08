# src/detectors.py
from typing import List, Dict
from pathlib import Path
import json, html, urllib.parse, re
from src.scanner.types import Payload

PROJECT_ROOT = Path(__file__).parent.parent.parent
SQL_ERRORS_PATH = PROJECT_ROOT / "data" / "sql_errors.json"
try:
    SQL_ERROR_LIST = [
        s.lower() for s in json.loads(SQL_ERRORS_PATH.read_text(encoding="utf-8"))
    ]
except Exception:
    SQL_ERROR_LIST = []


def detect_reflection(base, injected, payload: Payload) -> Dict:
    base_text = (base.body or "").lower()
    inj_text = (injected.body or "").lower()
    raw = (payload.payload or "").lower()

    if "alert(" in raw:
        candidate = "alert(1)"
    else:
        candidate = re.sub(r"[^a-z0-9]", "", raw)[:8]
        if len(candidate) < 4:
            return {"matched": False, "evidence": ""}

    variants = {candidate, html.escape(candidate), urllib.parse.quote(candidate)}
    for v in variants:
        if v in inj_text and v not in base_text:
            pos = inj_text.find(v)
            start = max(0, pos - 30)
            end = pos + len(v) + 30
            evidence = (injected.body or "")[start:end]
            return {"matched": True, "evidence": evidence}
    return {"matched": False, "evidence": ""}


def detect_sql_error(base, injected, payload: Payload) -> Dict:
    b = (base.body or "").lower()
    i = (injected.body or "").lower()
    for err in SQL_ERROR_LIST:
        if err and err in i and err not in b:
            return {"matched": True, "evidence": err}
    return {"matched": False, "evidence": ""}


def detect_time_delay(base, injected, payload: Payload) -> Dict:
    threshold_ms = 2000
    if (injected.response_time - base.response_time) > threshold_ms:
        return {
            "matched": True,
            "evidence": f"time delay: {injected.response_time - base.response_time:.0f} ms",
        }
    return {"matched": False, "evidence": ""}


DETECTORS = (detect_sql_error, detect_reflection, detect_time_delay)


def run_detectors(base, injected, payload: Payload) -> List[Dict]:
    result = []
    for detect in DETECTORS:
        try:
            res = detect(base, injected, payload)
            if res and res.get("matched"):
                result.append(res)
        except Exception as e:
            print(f"Problem during detecting: {str(e)}")
            continue
    return result
