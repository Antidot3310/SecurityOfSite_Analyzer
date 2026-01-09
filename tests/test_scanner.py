import os
import sys
import pytest
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.scanner.scanner import *
from src.scanner.types import Payload, VulnType, Severity, MatchType


def make_payload(payload="X", match=MatchType.REFLECTED):
    return Payload(
        payload_id="p",
        payload=payload,
        vuln_type=VulnType.XSS,
        severity=Severity.MEDIUM,
        match_type=match,
        evidence_patterns=[],
    )


def test_build_test_data_does_not_mutate():
    base = {"a": "1"}
    out = build_test_data(base, {"name": "q"}, make_payload("X"))
    assert base == {"a": "1"} and out["q"] == "X"


def test_build_base_line_fills_missing_values():
    res = build_base_line([{"name": "a", "value": "1"}, {"name": "b"}])
    assert res == {"a": "1", "b": ""}


class MockResp:
    def __init__(self):
        self.url = "http://example/"
        self.status_code = 200
        self.text = "OK" * 100


def test_send_form_request_success(monkeypatch):
    monkeypatch.setattr("requests.Session.request", lambda *a, **k: MockResp())
    form = {"action": "http://example", "method": "GET"}
    snap = send_form_request(form, {}, timeout=1, session=requests.Session())
    assert snap and snap.status_code == 200 and snap.url == "http://example/"


def test_send_form_request_handles_exception(monkeypatch):
    monkeypatch.setattr(
        "requests.Session.request",
        lambda *a, **k: (_ for _ in ()).throw(requests.RequestException("fail")),
    )
    assert not send_form_request(
        {"action": "http://bad"}, {}, session=requests.Session()
    )


def test_scan_field_happy_path(monkeypatch):
    base = ResponseSnapshot("u", 200, "base", 4, 100)
    inj = ResponseSnapshot("u", 200, "alert(1)", 8, 120)

    monkeypatch.setattr("src.scanner.scanner.send_form_request", lambda *a, **k: inj)
    monkeypatch.setattr(
        "src.scanner.detectors.run_detectors",
        lambda *a, **k: [{"matched": True, "evidence": "alert"}],
    )

    findings = scan_field(
        form={"form_id": 1, "action": "http://ex", "method": "GET"},
        inp={"name": "q", "type": "text"},
        base_line_snapshot=base,
        payloads=[make_payload("<script>alert(1)</script>")],
        base_data={"q": ""},
        rate_limit=0,
    )
    assert len(findings) == 1 and findings[0].field_name == "q"


def test_scan_field_ignores_unnamed_or_unsupported():
    base = ResponseSnapshot("u", 200, "base", 4, 100)
    payloads = [make_payload("x")]

    unnamed = scan_field({"form_id": 1}, {"type": "text"}, base, payloads, {}, 0)
    unsupported = scan_field(
        {"form_id": 1}, {"name": "a", "type": "submit"}, base, payloads, {}, 0
    )

    assert unnamed == [] and unsupported == []


def test_scan_form_baseline_missing(monkeypatch):
    monkeypatch.setattr("src.scanner.scanner.send_form_request", lambda *a, **k: None)
    form = {"form_id": "f", "action": "http://ex", "inputs": [{"name": "q"}]}
    assert scan_form(form, [make_payload("x")], rate_limit=0) == []


def test_scan_forms_session_reuse(monkeypatch):
    calls = 0

    def fake_scan_form(*a, **k):
        nonlocal calls
        calls += 1
        return []

    monkeypatch.setattr("src.scanner.scanner.scan_form", fake_scan_form)
    forms = [{"form_id": 1}, {"form_id": 2}]
    scan_forms(forms, [make_payload("x")], rate_limit=0)
    assert calls == 2
