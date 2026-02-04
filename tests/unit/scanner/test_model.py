import requests
from src.scanner.models import (
    build_base_line,
    build_test_data,
    send_form_request,
)
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
