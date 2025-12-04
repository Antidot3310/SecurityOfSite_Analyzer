from typing import List, Optional
import requests
import time

from .detectors import *
from .types import VulnType, Severity, MatchType, Payload
from .payloads import load_payloads


class Finding:

    def __init__(
        self, form_index: int, field_name: str, evidence: str, payload: Payload
    ):
        self.form_index = form_index
        self.field_name = field_name
        self.payload = payload
        self.evidence = evidence

    def to_dict(self):
        return {
            "form_index": self.form_index,
            "field_name": self.field_name,
            "payload": self.payload.to_dict(),
            "evidence": self.evidence,
        }


class ResponseSnapshot:
    def __init__(
        self, url: str, status_code: int, body: str, body_len: int, response_time: float
    ):
        self.url = url
        self.status_code = status_code
        self.body = body
        self.body_len = body_len
        self.response_time = response_time

    def to_dict(self):
        return {
            "url": self.url,
            "status_code": self.status_code,
            "body": self.body,
            "body_len": self.body_len,
            "response_time": self.response_time,
        }


def build_base_line(inputs: List[dict]) -> dict:
    data = {}
    for inp in inputs:
        name = inp.get("name")
        if not name:
            continue
        elif inp.get("value"):
            data[name] = inp.get("value", "")
    return data


def send_form_request(
    form: dict, data: dict, timeout: int = 8
) -> Optional[ResponseSnapshot]:
    action = form.get("action")
    if not action:
        print("Form has no action attribute")
        return None

    method = form.get("method", "GET").upper()
    headers = {"User-Agent": "MPV-Scanner/0.1"}

    try:
        start = time.monotonic()
        if method == "POST":
            resp = requests.post(action, data=data, timeout=timeout, headers=headers)
        else:
            resp = requests.get(action, params=data, timeout=timeout, headers=headers)
        elapsed = (time.monotonic() - start) * 1000
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None

    snapshot = ResponseSnapshot(
        url=resp.url,
        status_code=resp.status_code,
        body=resp.text[:512],
        body_len=len(resp.text),
        response_time=elapsed,
    )
    return snapshot


def scan_forms(forms: List[dict]) -> List[Finding]:
    findings = []
    RATE_LIMIT_MS = 500
    for form in forms:
        data = build_base_line(form["inputs"])
        base_line_snapshot = send_form_request(form, data)
        if not base_line_snapshot:
            continue
        for inp in form["inputs"]:
            name = inp.get("name")
            ftype = inp.get("type", "text").lower()
            if name is None:
                continue
            if ftype not in ("text", "search", "textarea", "url", "email", "tel"):
                continue
            for payload in payloads_list:
                test_data = data.copy()
                test_data[name] = payload.payload
                test_snapshot = send_form_request(form, test_data)
                sleep(RATE_LIMIT_MS / 1000)
                if not test_snapshot:
                    continue
                det_res = run_detectors(base_line_snapshot, test_snapshot, payload)
                for dr in det_res:
                    if dr["matched"]:
                        finding = {
                            "form_id": form.get("form_id"),
                            "field_name": name,
                            "payload_id": payload.payload_id,
                            "vuln_type": payload.vuln_type,
                            "severity": payload.severity,
                            "evidence": dr["evidence"],
                            "meta": {
                                "status": test_snapshot.status_code,
                                "time_ms": test_snapshot.response_time,
                                "body_len": test_snapshot.body_len,
                                "url": test_snapshot.url,
                            },
                        }
                        findings.append(finding)
    return findings
