from typing import List, Optional
import requests
from time import sleep, monotonic

import src.scanner.detectors as detector
from .types import Payload


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


def build_test_data(base_data: dict, input: dict, payload: Payload) -> dict:
    data = base_data.copy()
    name = input.get("name")
    data[name] = payload.payload
    return data


def build_base_line(inputs: List[dict]) -> dict:
    data = {}
    for inp in inputs:
        name = inp.get("name")
        if not name:
            continue
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
        start = monotonic()
        if method == "POST":
            resp = requests.post(action, data=data, timeout=timeout, headers=headers)
        else:
            resp = requests.get(action, params=data, timeout=timeout, headers=headers)
        elapsed = (monotonic() - start) * 1000
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


def scan_field(
    form: dict,
    inp: dict,
    base_line_snapshot: ResponseSnapshot,
    payloads: List[Payload],
    base_data: dict,
) -> List[Finding]:
    findings = []
    RATE_LIMIT_MS = 500

    name = inp.get("name")
    ftype = inp.get("type", "text").lower()
    if not name or ftype not in ("text", "search", "textarea", "url", "email", "tel"):
        return []

    for payload in payloads:
        test_data = build_test_data(base_data, inp, payload)
        test_snapshot = send_form_request(form, test_data)
        sleep(RATE_LIMIT_MS / 1000)
        if not test_snapshot:
            continue

        det_res = detector.run_detectors(
            base=base_line_snapshot, injected=test_snapshot, payload=payload
        )
        for dr in det_res:
            if dr["matched"]:
                findings.append(
                    Finding(
                        form_index=form.get("form_id"),
                        field_name=name,
                        payload=payload,
                        evidence=dr.get("evidence"),
                    )
                )
    return findings


def scan_form(form: dict, payloads: List[Payload]) -> List[Finding]:
    findings = []
    inputs = form.get("inputs", [])
    base_data = build_base_line(inputs)
    base_line_snapshot = send_form_request(form, base_data)
    if not base_line_snapshot:
        return []

    for inp in inputs:
        findings.extend(
            scan_field(
                form=form,
                inp=inp,
                payloads=payloads,
                base_line_snapshot=base_line_snapshot,
                base_data=base_data,
            )
        )

    return findings


def scan_forms(forms: List[dict], payloads: List[Payload]) -> List[Finding]:
    findings = []
    for form in forms:
        findings.extend(scan_form(form=form, payloads=payloads))
    return findings
