import pytest
from src.scanner.scanner import (
    build_test_data,
    build_base_line,
    scan_field,
    send_form_request,
    ResponseSnapshot,
)
from src.scanner.types import Payload, MatchType, VulnType, Severity
from src.scanner.detectors import run_detectors


def test_build_test_data_copy():
    base = {"a": "1"}
    inp = {"name": "q"}
    payload = Payload(
        "p1", "XVAL", VulnType.XSS, Severity.MEDIUM, MatchType.REFLECTED, []
    )
    out = build_test_data(base, inp, payload)
    assert out is not base
    assert "q" in out and out["q"] == "XVAL"
    assert "q" not in base


def test_build_base_line_includes_empty_values():
    inputs = [{"name": "a", "value": "1"}, {"name": "b"}]
    res = build_base_line(inputs)
    assert res["a"] == "1"
    assert res["b"] == ""


def test_scan_field_integration(monkeypatch):
    form = {
        "action": "http://example",
        "method": "POST",
        "form_id": "f1",
        "inputs": [{"name": "q", "type": "text"}],
    }
    inp = {"name": "q", "type": "text"}

    base_data = {"q": ""}
    base_snapshot = ResponseSnapshot(
        url="http://example",
        status_code=200,
        body="base",
        body_len=4,
        response_time=100,
    )
    injected_snapshot = ResponseSnapshot(
        url="http://example",
        status_code=200,
        body="<script>alert(1)</script>",
        body_len=30,
        response_time=110,
    )

    def fake_send_form_request(form_arg, data_arg, timeout=8):
        if data_arg == base_data:
            return base_snapshot
        return injected_snapshot

    monkeypatch.setattr("src.scanner.scanner.send_form_request", fake_send_form_request)

    def fake_run_detectors(base, injected, payload):
        return [{"detector": "reflection", "matched": True, "evidence": "alert(1)"}]

    monkeypatch.setattr("src.scanner.detectors.run_detectors", fake_run_detectors)

    payloads = [
        Payload(
            "p1",
            "<script>alert(1)</script>",
            VulnType.XSS,
            Severity.MEDIUM,
            MatchType.REFLECTED,
            [],
        )
    ]

    findings = scan_field(
        form=form,
        inp=inp,
        base_data=base_data,
        base_line_snapshot=base_snapshot,
        payloads=payloads,
    )
    assert isinstance(findings, list)
    assert len(findings) == 1
    f = findings[0]
    assert f.field_name == "q"
    assert f.payload.payload == "<script>alert(1)</script>"
    assert "alert" in f.evidence
