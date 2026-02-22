import pytest
from src.agregator.rulebased import (
    aggregate_findings,
    group_key_for_finding,
    compute_group_score,
    DEFAULT_RULES,
)


def make_finding(
    url="http://t",
    form_index="f",
    field_name="q",
    payload_index="p1",
    severity="HIGH",
    evidence="",
    response_time=100,
):
    return {
        "url": url,
        "form_index": form_index,
        "field_name": field_name,
        "payload_index": payload_index,
        "payload": "p",
        "vulnerability_type": "SQLI",
        "severity": severity,
        "match_type": "BOOLEAN",
        "evidence": evidence,
        "response_time": response_time,
        "body_length": 10,
    }


def test_group_key_for_finding_basic():
    f = make_finding(url="u", form_index="form1", field_name="user")
    assert group_key_for_finding(f) == "u|form1|user"


def test_aggregate_single_finding():
    f = make_finding()
    res = aggregate_findings([f])
    assert res["summary"]["total_findings"] == 1
    assert res["summary"]["total_groups"] == 1
    g = list(res["groups"].values())[0]
    assert g["count"] == 1
    assert g["unique_payloads"] == 1
    assert g["score"] >= 0


def test_handle_empty_input():
    res = aggregate_findings([])
    assert res["summary"]["total_findings"] == 0
    assert res["summary"]["total_groups"] == 0


def test_grouping_merges_same_field():
    f1 = make_finding(payload_index="p1")
    f2 = make_finding(payload_index="p2")
    res = aggregate_findings([f1, f2])
    assert res["summary"]["total_findings"] == 2
    assert res["summary"]["total_groups"] == 1
    g = list(res["groups"].values())[0]
    assert g["score"] <= 100
