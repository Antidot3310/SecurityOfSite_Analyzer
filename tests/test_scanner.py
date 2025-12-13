from src.scanner.scanner import (
    build_test_data,
    build_base_line,
    scan_field,
    ResponseSnapshot,
)
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.scanner.types import Payload, VulnType, Severity, MatchType


def test_build_test_data_does_not_mutate():
    base = {"a": "1"}
    inp = {"name": "q"}
    payload = Payload("p", "X", VulnType.XSS, Severity.LOW, MatchType.REFLECTED, [])

    out = build_test_data(base, inp, payload)

    assert base == {"a": "1"}
    assert out["q"] == "X"


def test_build_base_line_fills_missing_values():
    inputs = [{"name": "a", "value": "1"}, {"name": "b"}]
    res = build_base_line(inputs)

    assert res == {"a": "1", "b": ""}


def test_scan_field_happy_path(monkeypatch):
    form = {"form_id": 1}
    inp = {"name": "q", "type": "text"}
    base_data = {"q": ""}
    payload = Payload(
        "p",
        "<script>alert(1)</script>",
        VulnType.XSS,
        Severity.MEDIUM,
        MatchType.REFLECTED,
        [],
    )

    base_snap = ResponseSnapshot("u", 200, "base", 4, 100)
    inj_snap = ResponseSnapshot("u", 200, "alert(1)", 8, 120)

    monkeypatch.setattr(
        "src.scanner.scanner.send_form_request",
        lambda *a, **k: inj_snap,
    )
    monkeypatch.setattr(
        "src.scanner.detectors.run_detectors",
        lambda *a, **k: [{"matched": True, "evidence": "alert"}],
    )

    res = scan_field(
        form=form,
        inp=inp,
        base_line_snapshot=base_snap,
        payloads=[payload],
        base_data=base_data,
        rate_limit=0,
    )

    assert len(res) == 1
    assert res[0].field_name == "q"
