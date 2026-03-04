"""
Модуль реализует логику сканирования веб-форм на уязвимости.

Функции:
    scan_field  - сканирование одного поля формы с перебором payloads
    scan_form   - сканирование всех полей одной формы
    scan_forms  - сканирование списка форм с использованием общей сессии
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
    field: dict,
    base_line_snapshot: ResponseSnapshot,
    payloads: List[Payload],
    base_data: dict,
    rate_limit: float = RATE_LIMIT,
    session: Optional[requests.Session] = None,
) -> List[Finding]:
    """
    Сканирует одно поле формы, перебирая список полезных нагрузок.

    Параметры:
        form: словарь, представляющий форму
        field: словарь поля
        base_line_snapshot: базоввый ответ
        payloads: список объектов Payload
        base_data: словарь базовых данных для отправки
        rate_limit: задержка между запросами в секундах
        session: опциональная сессия requests для переиспользования соединений

    Возвращает:
        Список обнаруженных уязвимостей (объекты Finding).
    """
    findings: List[Finding] = []

    field_name = field.get("name")
    field_type = (field.get("type") or "text").lower()

    if not field_name or field_type not in ALLOWED_INPUT_TYPES:
        logger.debug(
            "Skipping field",
            extra={
                "form_id": form.get("form_id"),
                "field_name": field_name,
                "field_type": field_type,
            },
        )
        return findings

    for payload in payloads:
        try:
            logger.debug(
                "Sending payload",
                extra={
                    "form_id": form.get("form_id"),
                    "field": field_name,
                    "payload_id": payload.payload_id,
                    "payload": payload.payload,
                },
            )

            test_data = build_test_data(base_data, field, payload)
            test_snapshot = send_form_request(form, test_data, session=session)

            if not test_snapshot:
                logger.warning(
                    "No response for payload, skipping",
                    extra={
                        "form_id": form.get("form_id"),
                        "field": field_name,
                        "payload_id": payload.payload_id,
                    },
                )
                continue

            logger.debug(
                "Test snapshot received",
                extra={
                    "form_id": form.get("form_id"),
                    "status": test_snapshot.status_code,
                    "body_len": len(test_snapshot.body),
                    "response_time": test_snapshot.response_time,
                },
            )

            dets = detector.run_detectors(base_line_snapshot, test_snapshot, payload)
            for d in dets:
                if d.get("matched"):
                    findings.append(
                        Finding(
                            form_index=form.get("form_id"),
                            field_name=field_name,
                            evidence=d.get("evidence") or "",
                            payload=payload,
                            response_time_ms=test_snapshot.response_time * 1000,
                            body_len=len(test_snapshot.body),
                            url=test_snapshot.url,
                        )
                    )

            if rate_limit > 0:
                sleep(rate_limit)

        except Exception as e:
            logger.exception(
                "Error while scanning field with payload",
                extra={
                    "form_id": form.get("form_id"),
                    "field": field_name,
                    "payload_id": payload.payload_id,
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
    Сканирует все поля одной формы.


    Параметры:
        form: словарь, представляющий форму
        payloads: список объектов Payload
        session: опциональная сессия requests
        rate_limit: задержка между запросами

    Возвращает:
        Список уязвимостей, найденных во всех полях формы.
    """
    inputs = form.get("inputs", [])
    if not inputs:
        logger.debug(
            "Form has no inputs, skipping", extra={"form_id": form.get("form_id")}
        )
        return []

    base_data = build_base_line(inputs)
    base_snapshot = send_form_request(form, base_data, session=session)

    if not base_snapshot:
        logger.warning(
            "Failed to obtain baseline response for form",
            extra={"form_id": form.get("form_id")},
        )
        return []

    logger.debug(
        "Baseline created",
        extra={
            "form_id": form.get("form_id"),
            "status": base_snapshot.status_code,
            "body_len": len(base_snapshot.body),
            "response_time": base_snapshot.response_time,
        },
    )

    findings: List[Finding] = []
    for field in inputs:
        try:
            field_findings = scan_field(
                form,
                field,
                base_snapshot,
                payloads,
                base_data,
                rate_limit,
                session,
            )
            findings.extend(field_findings)
        except Exception as e:
            logger.exception(
                "Error scanning field in form",
                extra={
                    "form_id": form.get("form_id"),
                    "field_name": field.get("name"),
                    "error": str(e),
                },
            )
            continue

    return findings


def scan_forms(
    forms: List[dict],
    payloads: List[Payload],
    rate_limit,
    session: Optional[requests.Session],
) -> List[Finding]:
    """
    Сканирует список форм, используя общую сессию requests.

    Параметры:
        forms: список словарей, представляющих формы
        payloads: список объектов Payload
        rate_limit: задержка между запросами (по умолчанию из конфига)

    Возвращает:
        Объединённый список уязвимостей, найденных во всех формах.
    """
    logger.info("Starting scan of %d forms", len(forms))
    all_findings: List[Finding] = []
    if session is None:
        session = requests.Session()

    try:
        for idx, form in enumerate(forms):
            form_id = form.get("form_id", f"index_{idx}")
            try:
                form_findings = scan_form(form, payloads, session, rate_limit)
                all_findings.extend(form_findings)
                logger.info(
                    "Finished scanning form",
                    extra={
                        "form_id": form_id,
                        "findings_in_form": len(form_findings),
                        "total_findings_so_far": len(all_findings),
                    },
                )
            except Exception as e:
                logger.exception(
                    "Unexpected error while scanning form",
                    extra={"form_id": form_id, "error": str(e)},
                )
                continue
    finally:
        session.close()
    logger.info(
        "Scan completed",
        extra={"forms_processed": len(forms), "total_findings": len(all_findings)},
    )
    return all_findings
