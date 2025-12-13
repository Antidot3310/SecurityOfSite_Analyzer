from dataclasses import dataclass, asdict
from time import sleep, monotonic
from typing import List, Optional
import requests

import src.scanner.detectors as detector
from .types import Payload


@dataclass
class Finding:
    form_index: int
    field_name: str
    evidence: str
    payload: Payload

    def to_dict(self):
        return asdict(self)


@dataclass
class ResponseSnapshot:
    url: str
    status_code: int
    body: str
    body_len: int
    response_time: float

    def to_dict(self):
        return asdict(self)


ALLOWED_INPUT_TYPES = {"text", "search", "textarea", "url", "email", "tel"}


def build_test_data(base_data: dict, input_field: dict, payload: Payload) -> dict:
    data = base_data.copy()
    name = input_field.get("name")
    if name:
        data[name] = payload.payload
    return data


def build_base_line(inputs: List[dict]) -> dict:
    return {inp["name"]: inp.get("value", "") for inp in inputs if inp.get("name")}


def send_form_request(
    form: dict,
    data: dict,
    timeout: int = 8,
    session: Optional[requests.Session] = None,
) -> Optional[ResponseSnapshot]:

    action = form.get("action")
    if not action:
        print("Form has no action attribute")
        return None

    method = (form.get("method") or "GET").upper()
    headers = {"User-Agent": "MVP-Scanner/0.1"}

    own_session = False
    if session is None:
        session = requests.Session()
        own_session = True

    try:
        start = monotonic()
        if method == "POST":
            resp = session.request(
                "POST", action, data=data, timeout=timeout, headers=headers
            )
        else:
            resp = session.request(
                "GET", action, params=data, timeout=timeout, headers=headers
            )
        elapsed_ms = (monotonic() - start) * 1000
    except requests.RequestException as e:
        print("Request failed for %s: %s", action, e)
        if own_session:
            session.close()
        return None

    snapshot = ResponseSnapshot(
        url=resp.url,
        status_code=resp.status_code,
        body=resp.text[:512],
        body_len=len(resp.text),
        response_time=elapsed_ms,
    )

    if own_session:
        session.close()
    return snapshot


def scan_field(
    form: dict,
    inp: dict,
    base_line_snapshot: ResponseSnapshot,
    payloads: List[Payload],
    base_data: dict,
    rate_limit: float = 0.5,
    session: Optional[requests.Session] = None,
) -> List[Finding]:

    findings: List[Finding] = []

    name = inp.get("name")
    ftype = (inp.get("type") or "text").lower()
    if not name or ftype not in ALLOWED_INPUT_TYPES:
        return findings

    for payload in payloads:
        test_data = build_test_data(base_data, inp, payload)
        test_snapshot = send_form_request(form, test_data, session=session)
        sleep(rate_limit)
        if not test_snapshot:
            continue

        det_res = detector.run_detectors(
            base=base_line_snapshot, injected=test_snapshot, payload=payload
        )
        for dr in det_res:
            if dr.get("matched"):
                findings.append(
                    Finding(
                        form_index=form.get("form_id"),
                        field_name=name,
                        payload=payload,
                        evidence=dr.get("evidence"),
                    )
                )

    return findings


def scan_form(
    form: dict, payloads: List[Payload], session: Optional[requests.Session] = None
) -> List[Finding]:
    findings: List[Finding] = []
    inputs = form.get("inputs", [])
    base_data = build_base_line(inputs)
    base_line_snapshot = send_form_request(form, base_data, session=session)
    if not base_line_snapshot:
        return findings

    for inp in inputs:
        findings.extend(
            scan_field(
                form=form,
                inp=inp,
                payloads=payloads,
                base_line_snapshot=base_line_snapshot,
                base_data=base_data,
                session=session,
            )
        )

    return findings


def scan_forms(forms: List[dict], payloads: List[Payload]) -> List[Finding]:
    with requests.Session() as session:
        findings: List[Finding] = []
        for form in forms:
            findings.extend(scan_form(form=form, payloads=payloads, session=session))
    return findings
