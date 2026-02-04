import pytest
from src.scanner.detectors import (
    detect_sql_error,
    detect_patterns,
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


@pytest.mark.parametrize(
    "base_body,inj_body,expected",
    [
        ("ok", f"error happened: {SQL_ERROR_LIST[0]}", True),
        ("ok", "still ok", False),
    ],
)
def test_detect_sql_error(base_body, inj_body, expected):
    base = snap(base_body)
    inj = snap(inj_body)

    res = detect_sql_error(base, inj, payload("' OR 1=1"))
    assert res["matched"] == expected


@pytest.mark.parametrize(
    "base_body,inj_body,expected",
    [
        ("hello", "<script>alert(1)</script>", True),  # positive
        ("hello", "just text", False),  # negative
        (
            "<script>alert(1)</script>",
            "<script>alert(1)</script>",
            False,
        ),  # base == inj
    ],
)
def test_detect_patterns(base_body, inj_body, expected):
    base = snap(base_body)
    inj = snap(inj_body)

    res = detect_patterns(base, inj, payload("<script>alert(1)</script>"))
    assert res["matched"] is expected


@pytest.mark.parametrize(
    "base_time,inj_time,expected",
    [
        (100, 2600, True),
        (100, 900, False),
    ],
)
def test_detect_time_delay(base_time, inj_time, expected):
    base = snap("ok", base_time)
    inj = snap("ok", inj_time)

    res = detect_time_delay(base, inj, payload("sleep", MatchType.TIME_BASED))
    assert res["matched"] == expected


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
