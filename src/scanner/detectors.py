import os
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root not in sys.path:
    sys.path.insert(0, root)

from scanner.scanner import ResponseSnapshot, Payload, Finding
from typing import List, Optional


def detect_reflection():
    pass


def detect_sql_error():
    pass


def detect_time_delay():
    pass


def run_detectors(
    base_snapshot: ResponseSnapshot, test_snapshot: ResponseSnapshot, payload: Payload
) -> List[Finding]:
    detectors = [detect_sql_error, detect_reflection, detect_time_delay]
    for detector in detectors:
        dr = detector(base_snapshot, test_snapshot, payload)
        if dr and dr["matched"]:
            finding = Finding(
                form_index=None,
                field_name=None,
                payload=payload,
                evidence=dr["evidence"],
            )
        return finding
    return None
