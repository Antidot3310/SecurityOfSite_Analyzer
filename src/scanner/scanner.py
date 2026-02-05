"""
Модуль реализует логику сканирования целевого ресурса
на уязвимости (для каждого отдельного поля запускает детекторы)

Функции:
    scan_field()
    scan_form()
    scan_forms()
"""

import requests
from time import sleep
from typing import List, Optional

import src.scanner.detectors as detector
from .types import Payload
from .models import (
    Finding,
    ResponseSnapshot,
    build_base_line,
    build_test_data,
    send_form_request,
)
from src.config import RATE_LIMIT
from src.logger import get_logger

logger = get_logger(__name__)


ALLOWED_INPUT_TYPES = {"text", "search", "textarea", "url", "email", "tel"}


def scan_field(
    form: dict,
    inp: dict,
    base_line_snapshot: ResponseSnapshot,
    payloads: List[Payload],
    base_data: dict,
    rate_limit: float = 0.5,
    session: Optional[requests.Session] = None,
) -> List[Finding]:
    """
    Сканирует каждое отдельное поле
    """
    findings: List[Finding] = []

    name = inp.get("name")
    # Отсеиваем неподдерживаемые типы
    if not name or (inp.get("type") or "text").lower() not in ALLOWED_INPUT_TYPES:
        logger.warning(
            "skipping field",
            extra={
                "form_id": form.get("form_id"),
                "field": name,
                "type": inp.get("type") or "text",
            },
        )
        return findings

    for payload in payloads:
        try:
            # Логирование отправки полезной нагрузки
            logger.debug(
                "sending payload",
                extra={
                    "form_id": form.get("form_id"),
                    "field": inp.get("name"),
                    "payload_id": payload.payload_id,
                    "payload": payload.payload,
                },
            )
            # Составление, отправка запроса с payload, засекание времени
            test_data = build_test_data(base_data, inp, payload)
            test_snapshot = send_form_request(form, test_data, session=session)
            # Логирование полученного ответа
            if test_snapshot:
                logger.debug(
                    "test snapshot created",
                    extra={
                        "form_id": form.get("form_id"),
                        "status": test_snapshot.status_code,
                        "body_len": len(test_snapshot.body),
                        "response_time": test_snapshot.response_time,
                    },
                )

            if rate_limit:
                sleep(rate_limit)
            if not test_snapshot:
                continue

            # Проводим детектирование
            dets = detector.run_detectors(base_line_snapshot, test_snapshot, payload)
            for d in dets:
                if d.get("matched"):
                    findings.append(
                        Finding(
                            form_index=form.get("form_id"),
                            field_name=name,
                            evidence=d.get("evidence") or "",
                            payload=payload,
                            response_time_ms=test_snapshot.response_time * 1000,
                            body_len=len(test_snapshot.body),
                            url=test_snapshot.url,
                        )
                    )
        except Exception as e:
            logger.exception(
                "scan_field error",
                extra={
                    "form_id": form.get("form_id"),
                    "field": name,
                    "payload": payload.payload,
                    "error": str(e),
                },
            )
            continue

    return findings


def scan_form(
    form: dict,
    payloads: List[Payload],
    session: Optional[requests.Session] = None,
    rate_limit: float = RATE_LIMIT,
) -> List[Finding]:
    """
    Сканирует отдельную форму
    На данном этапе отправляется базовый запрос
    """
    inputs = form.get("inputs", []) or []
    # Создание базовой линии
    base_data = build_base_line(inputs)
    base_snapshot = send_form_request(form, base_data, session=session)
    # Логирование результата создания базовой линии
    if base_snapshot:
        body_len = len(base_snapshot.body)
        logger.debug(
            "baseline created",
            extra={
                "form_id": form.get("form_id"),
                "status": base_snapshot.status_code,
                "body_len": body_len,
                "response_time": base_snapshot.response_time,
            },
        )
    if not base_snapshot:
        logger.warning(
            "Couldn't create baseline for form", extra={"form_id": form.get("form_id")}
        )
        return []

    findings: List[Finding] = []
    for inp in inputs:
        findings.extend(
            scan_field(
                form,
                inp,
                base_snapshot,
                payloads,
                base_data,
                rate_limit,
                session,
            )
        )
    return findings


def scan_forms(
    forms: List[dict], payloads: List[Payload], rate_limit: float = 1
) -> List[Finding]:
    """
    Сканирование списка форм
    """
    logger.info("Started scanning forms", extra={"forms_count": len(forms)})
    findings: List[Finding] = []
    with requests.Session() as session:
        for form in forms:
            try:
                findings.extend(scan_form(form, payloads, session, rate_limit))
                logger.info(
                    "Form scan finished",
                    extra={
                        "form_id": form.get("form_id"),
                        "findings_count": len(findings),
                    },
                )
            except Exception as e:
                logger.exception(
                    "Error scanning form",
                    extra={"form_id": form.get("form_id"), "error": str(e)},
                )
                continue
    logger.info("Finished scanning forms", extra={"forms_count": len(forms)})
    return findings
