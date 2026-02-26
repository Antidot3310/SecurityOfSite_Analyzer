"""import pytest
from src.agregator.rulebased import aggregate_findings, compute_group_score, DEFAULT_RULES


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


def test_grouping_creates_expected_keys():
    f1 = make_finding(url="http://1", form_index="1", field_name="1")
    f2 = make_finding(url="http://2", form_index="2", field_name="2")
    aggregated = aggregate_findings([f1, f2])
    assert aggregated["summary"]["total_groups"] == 2
    keys = list(aggregated["groups"].keys())
    keys[0] == "http://1|1|1"
    keys[1] == "http://2|2|2"

def test_score_computing():
    f = {
        "body_length": 66,
        "evidence": "<html><body> <iframe src=\"javascript:alert('XSS')\"",
        "field_name": "user",
        "finding_id": 19,
        "form_index": "sqli",
        "match_type": "DOM_BASED",
        "payload": "<iframe src=\"javascript:alert('XSS')\">",
        "payload_index": "xss9",
        "response_time": 3.796299999976327,
        "scan_id": 46,
        "severity": "MEDIUM",
        "url": "http://127.0.0.1:5000/dummy",
        "vuln_type": "XSS",
    }
    score, notes = compute_group_score([f], DEFAULT_RULES)
    assert score == 3"""