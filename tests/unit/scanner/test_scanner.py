from src.scanner.scanner import scan_forms, scan_form, scan_field
from src.scanner.models import ResponseSnapshot
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
