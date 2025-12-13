import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.scanner.detectors import (
    detect_sql_error,
    detect_reflection,
    detect_time_delay,
    run_detectors,
    SQL_ERROR_LIST,
)
from src.scanner.scanner import ResponseSnapshot
from src.scanner.types import Payload, MatchType, VulnType, Severity


def snap(body: str, time_ms=100):
    return ResponseSnapshot(
        url="http://t",
        status_code=200,
        body=body,
        body_len=len(body),
        response_time=time_ms,
    )


def payload(val: str, match=MatchType.REFLECTED):
    return Payload(
        "p",
        val,
        vuln_type=VulnType.XSS,
        severity=Severity.MEDIUM,
        match_type=match,
        evidence_patterns=[],
    )


def test_detect_sql_error_positive():
    if not SQL_ERROR_LIST:
        return None

    err = SQL_ERROR_LIST[0]
    base = snap("ok")
    inj = snap(f"error happened: {err}")

    res = detect_sql_error(base, inj, payload("' OR 1=1"))
    assert res["matched"] is True


def test_detect_reflection_positive():
    base = snap("hello")
    inj = snap("<script>alert(1)</script>")

    res = detect_reflection(base, inj, payload("<script>alert(1)</script>"))
    assert res["matched"] is True
    assert "alert" in res["evidence"]


def test_detect_time_delay_positive():
    base = snap("ok", 100)
    inj = snap("ok", 2600)

    res = detect_time_delay(base, inj, payload("sleep", MatchType.TIME_BASED))
    assert res["matched"] is True


def test_run_detectors_aggregates(monkeypatch):
    def d1(*a, **k):
        return {"matched": False}

    def d2(*a, **k):
        return {"matched": True, "evidence": "hit"}

    def d3(*a, **k):
        return {"matched": False}

    monkeypatch.setattr("src.scanner.detectors.DETECTORS", (d1, d2, d3))

    res = run_detectors(snap("b"), snap("i"), payload("x"))
    assert len(res) == 1
    assert res[0]["evidence"] == "hit"
