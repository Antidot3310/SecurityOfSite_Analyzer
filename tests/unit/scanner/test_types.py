from src.scanner.types import Payload, VulnType, Severity, MatchType


def test_payload_to_dict():
    payload = Payload(
        payload_id="p1",
        payload="test",
        vuln_type=VulnType.XSS,
        severity=Severity.HIGH,
        match_type=MatchType.REFLECTED,
        evidence_patterns=["x"],
    )

    d = payload.to_dict()

    assert d["payload_id"] == "p1"
    assert d["payload"] == "test"
    assert d["vuln_type"] == "XSS"
    assert d["severity"] == "HIGH"
    assert d["match_type"] == "REFLECTED"
    assert d["evidence_patterns"] == ["x"]
