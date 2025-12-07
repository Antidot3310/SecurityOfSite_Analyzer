from src.scanner.detectors import (
    detect_sql_error,
    detect_reflection,
    detect_time_delay,
    run_detectors,
    SQL_ERROR_LIST,
)
import pytest

from src.scanner.scanner import ResponseSnapshot
from src.scanner.types import Payload, MatchType, VulnType, Severity


def make_snapshot(body: str, time_ms: float = 100.0) -> ResponseSnapshot:
    return ResponseSnapshot(
        url="http://test",
        status_code=200,
        body=body,
        body_len=len(body),
        response_time=time_ms,
    )


def make_payload(
    payload_str: str,
    match_type=MatchType.REFLECTED,
    vuln_type=VulnType.XSS,
    severity=Severity.MEDIUM,
):
    return Payload(
        payload_id="p1",
        payload=payload_str,
        vuln_type=vuln_type,
        severity=severity,
        match_type=match_type,
        evidence_patterns=[],
    )


def test_detect_sql_error_positive():
    base = make_snapshot("Welcome page")
    inj = make_snapshot(
        "Something went wrong: You have an error in your SQL syntax near '...'", 120
    )
    payload = make_payload(
        "' OR '1'='1",
        match_type=MatchType.ERROR_BASED,
        vuln_type=VulnType.SQLI,
        severity=Severity.HIGH,
    )

    res = detect_sql_error(base, inj, payload)
    assert isinstance(res, dict)
    assert res["matched"] is True
    assert any(err in inj.body.lower() for err in SQL_ERROR_LIST)


def test_detect_sql_error_negative_when_in_base():
    base = make_snapshot(
        "You have an error in your SQL syntax near '...'"
    )  # error already present
    inj = make_snapshot("You have an error in your SQL syntax near '...'")
    payload = make_payload(
        "' OR '1'='1",
        match_type=MatchType.ERROR_BASED,
        vuln_type=VulnType.SQLI,
        severity=Severity.HIGH,
    )

    res = detect_sql_error(base, inj, payload)
    assert isinstance(res, dict)
    assert res["matched"] is False


def test_detect_reflection_positive():
    base = make_snapshot("<html>hello</html>")
    inj = make_snapshot("<html>hello<script>alert(1)</script></html>")
    payload = make_payload(
        "<script>alert(1)</script>",
        match_type=MatchType.REFLECTED,
        vuln_type=VulnType.XSS,
    )

    res = detect_reflection(base, inj, payload)
    assert res["matched"] is True
    assert "alert(1)" in res["evidence"]


def test_detect_reflection_negative_when_in_base():
    base = make_snapshot("<html><script>alert(1)</script></html>")
    inj = make_snapshot("<html><script>alert(1)</script></html>")
    payload = make_payload(
        "<script>alert(1)</script>",
        match_type=MatchType.REFLECTED,
        vuln_type=VulnType.XSS,
    )

    res = detect_reflection(base, inj, payload)
    assert res["matched"] is False


def test_detect_time_delay_positive():
    base = make_snapshot("<html>ok</html>", time_ms=100)
    inj = make_snapshot("<html>ok</html>", time_ms=2600)
    payload = make_payload(
        "' OR SLEEP(2)--", match_type=MatchType.TIME_BASED, vuln_type=VulnType.SQLI
    )

    res = detect_time_delay(base, inj, payload)
    assert res["matched"] is True
    assert "time" in res["evidence"].lower()


def test_run_detectors_calls_all_and_aggregates(monkeypatch):
    base = make_snapshot("base")
    inj = make_snapshot("inj alert(1)")
    payload = make_payload(
        "<script>alert(1)</script>",
        match_type=MatchType.REFLECTED,
        vuln_type=VulnType.XSS,
    )

    def fake_sql(base_, inj_, payload_):
        return {"matched": False, "evidence": ""}

    def fake_ref(base_, inj_, payload_):
        return {"matched": True, "evidence": "reflected: alert(1)"}

    def fake_time(base_, inj_, payload_):
        return {"matched": False, "evidence": ""}

    monkeypatch.setattr("src.scanner.detectors.detect_sql_error", fake_sql)
    monkeypatch.setattr("src.scanner.detectors.detect_reflection", fake_ref)
    monkeypatch.setattr("src.scanner.detectors.detect_time_delay", fake_time)

    results = run_detectors(base, inj, payload)
    assert isinstance(results, list)
    assert any("reflected" in r.get("evidence", "") for r in results)
