from dataclasses import dataclass, asdict
from time import sleep, monotonic
from typing import List, Optional, Any
import logging
import requests

import src.scanner.detectors as detector
from .types import Payload

logger = logging.getLogger(__name__)

BODY_PREVIEW = 512
ALLOWED_INPUT_TYPES = {"text", "search", "textarea", "url", "email", "tel"}


@dataclass
class Finding:
    form_index: Optional[Any]
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


def build_test_data(base_data: dict, input_field: dict, payload: Payload) -> dict:
    d = dict(base_data)
    name = input_field.get("name")
    if name:
        d[name] = payload.payload
    return d


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
        logger.debug("Form has no action attribute: %s", form.get("form_id"))
        return None

    method = (form.get("method") or "GET").upper()
    headers = {"User-Agent": "MVP-Scanner/0.1"}

    def _make_request(s: requests.Session):
        try:
            start = monotonic()
            resp = s.request(method, action, params=None if method == "POST" else data,
                             data=data if method == "POST" else None,
                             timeout=timeout, headers=headers)
            elapsed_ms = (monotonic() - start) * 1000
        except requests.RequestException as e:
            logger.warning("Request failed for %s: %s", action, e)
            return None
        return ResponseSnapshot(
            url=getattr(resp, "url", action),
            status_code=getattr(resp, "status_code", resp.status_code),
            body=(resp.text or "")[:BODY_PREVIEW],
            body_len=len(resp.text or ""),
            response_time=elapsed_ms,
        )

    if session is None:
        with requests.Session() as s:
            return _make_request(s)
    return _make_request(session)


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
    if not name or (inp.get("type") or "text").lower() not in ALLOWED_INPUT_TYPES:
        return findings

    for payload in payloads:
        try:
            test_data = build_test_data(base_data, inp, payload)
            test_snapshot = send_form_request(form, test_data, session=session)
            if rate_limit:
                sleep(rate_limit)
            if not test_snapshot:
                continue

            dets = detector.run_detectors(base_line_snapshot, test_snapshot, payload)
            for d in dets:
                if d.get("matched"):
                    findings.append(
                        Finding(
                            form_index=form.get("form_id"),
                            field_name=name,
                            evidence=d.get("evidence") or "",
                            payload=payload,
                        )
                    )
        except Exception:
            logger.exception("scan_field error for field=%s payload=%s", name, getattr(payload, "payload", None))
            continue

    return findings


def scan_form(
    form: dict,
    payloads: List[Payload],
    session: Optional[requests.Session] = None,
    rate_limit: float = 0.5,
) -> List[Finding]:
    inputs = form.get("inputs", []) or []
    base_data = build_base_line(inputs)
    base_snapshot = send_form_request(form, base_data, session=session)
    if not base_snapshot:
        logger.info("Couldn't create baseline for form %s", form.get("form_id"))
        return []
    findings: List[Finding] = []
    for inp in inputs:
        findings.extend(
            scan_field(form, inp, base_snapshot, payloads, base_data, rate_limit=rate_limit, session=session)
        )
    return findings


def scan_forms(forms: List[dict], payloads: List[Payload], rate_limit: float = 0.5) -> List[Finding]:
    findings: List[Finding] = []
    with requests.Session() as session:
        for form in forms:
            try:
                findings.extend(scan_form(form, payloads, session=session, rate_limit=rate_limit))
            except Exception:
                logger.exception("error scanning form %s", form.get("form_id"))
    return findings
