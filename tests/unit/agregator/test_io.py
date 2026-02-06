import pytest
from src.agregator.io import normalize_finding, export_findings, sample_findings
from src.scanner.types import Payload, VulnType, MatchType, Severity
from src.scanner.models import Finding


def make_payload(pid="p1", payload="VAL", vuln="XSS", sev="HIGH", mtype="REFLECTED"):
    return Payload(
        payload_id=pid,
        payload=payload,
        vuln_type=VulnType(vuln),
        severity=Severity(sev),
        match_type=MatchType(mtype),
        evidence_patterns=["evidence1", "evidence2"],
    )


def make_finding(payload=None):
    if payload is None:
        payload = make_payload()
    return Finding(
        form_index="f1",
        field_name="q",
        evidence="found",
        payload=payload,
        response_time_ms=123.4,
        body_len=321,
        url="http://t",
    )


def test_normalize_field_values_and_ids():
    f = make_finding(
        payload=make_payload(pid="sqli1", payload="OR 1=1", vuln="SQLI", sev="HIGH")
    )
    norm = normalize_finding(f, idx=7, scan_id=99)
    assert norm["finding_id"] == 7
    assert norm["scan_id"] == 99
    assert norm["payload_index"] == "sqli1"
    assert norm["payload"] == "OR 1=1"
    assert norm["vuln_type"] == "SQLI"
    assert norm["severity"] == "HIGH"
    assert norm["match_type"] == "REFLECTED"
    assert norm["response_time"] == 123.4
    assert norm["body_length"] == 321
    assert norm["url"] == "http://t"


@pytest.mark.parametrize("count", [0, 1, 3])
def test_export_and_sample_basic(count):
    findings = [make_finding(payload=make_payload(pid=f"p{i}")) for i in range(count)]
    normalized = export_findings(findings, scan_id=10)
    assert isinstance(normalized, list)
    assert len(normalized) == count
    s = sample_findings(normalized, n=2)
    assert s == normalized[:2]


def test_normalize_handles_missing_attrs():
    payload = {
        "payload_id": "p1",
        "payload": "x",
        "vuln_type": "XSS",
    }
    f = make_finding(payload=make_payload(pid="p1", payload="p", vuln="XSS"))
    norm = normalize_finding(f, idx=1, scan_id=None)
    assert norm["finding_id"] == 1
    assert norm["scan_id"] is None



@pytest.mark.parametrize("n, expected_len", [(0, 0), (1, 1), (5, 3)])
def test_sample_parametrized(n, expected_len):
    findings = [make_finding(payload=make_payload(pid=f"p{i}")) for i in range(3)]
    normalized = export_findings(findings, scan_id=1)
    out = sample_findings(normalized, n=n)
    assert len(out) == expected_len
