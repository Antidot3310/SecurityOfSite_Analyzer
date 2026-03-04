"""
Модуль предоставляет абстракции для представления уязвимостей и ответов сервера.

Классы:
    Finding           – результат срабатывания детектора.
    ResponseSnapshot  – «снимок» ответа сервера (статус, тело, время).

Функции:
    build_base_line   – создаёт словарь с базовыми значениями полей формы.
    build_test_data   – модифицирует базовые данные, подставляя payload в указанное поле.
    send_form_request – отправляет заполненную форму и возвращает ResponseSnapshot.
"""

import requests
from typing import List, Optional
from dataclasses import dataclass, asdict
from time import monotonic
from .types import Payload
from src.config import REQUEST_TIMEOUT, DEFAULT_HEADER
from src.logger import get_logger

logger = get_logger(__name__)

BODY_PREVIEW = 512


@dataclass
class Finding:
    """
    Представляет найденную уязвимость.

    Атрибуты:
        form_index: идентификатор формы
        field_name: имя поля, в которое вставлялся payload
        evidence:   фрагмент ответа, подтверждающий уязвимость
        payload:    объект использованной полезной нагрузки
        response_time_ms: время ответа сервера в миллисекундах
        body_len:   полная длина тела ответа
        url:        итоговый URL
    """

    form_index: Optional[str]
    field_name: str
    evidence: str
    payload: Payload
    response_time_ms: float
    body_len: int
    url: str

    def to_dict(self):
        return {
            "form_index": self.form_index,
            "field_name": self.field_name,
            "evidence": self.evidence,
            "payload": self.payload.to_dict(),
            "response_time_ms": self.response_time_ms,
            "body_len": self.body_len,
            "url": self.url,
        }


@dataclass
class ResponseSnapshot:
    """
    Снимок ответа сервера.

    Атрибуты:
        url:           итоговый URL
        status_code:   HTTP-код ответа
        body:          тело
        body_len:      полная длина тела
        response_time: время получения ответа в секундах
    """

    url: str
    status_code: int
    body: str
    body_len: int
    response_time: float

    def to_dict(self):
        return asdict(self)


def build_base_line(inputs: List[dict]) -> dict:
    data = {}

    for inp in inputs:
        name = inp.get("name")
        if not name:
            continue
        value = inp.get("value") or name
        data[name] = value

    if "Submit" not in data:
        data["Submit"] = "Submit"

    return data


def build_test_data(base_data: dict, input_field: dict, payload: Payload) -> dict:
    """
    Создаёт копию базовых данных и подставляет полезную нагрузку в указанное поле.

    Параметры:
        base_data:    исходные данные
        input_field:  словарь поля
        payload:      объект Payload
    """
    data = dict(base_data)
    name = input_field.get("name")
    if name:
        data[name] = payload.payload
    return data


def send_form_request(
    form: dict,
    data: dict,
    timeout: int = REQUEST_TIMEOUT,
    session: Optional[requests.Session] = None,
) -> Optional[ResponseSnapshot]:
    """
    Отправляет заполненную форму и возвращает снимок ответа.

    Параметры:
        form:    словарь, представляющий форму
        data:    словарь с данными для отправки
        timeout: таймаут запроса в секундах
        session: опциональная сессия requests

    Возвращает:
        Объект ResponseSnapshot или None, если запрос не удался.
    """
    action = form.get("action")

    method = (form.get("method") or "GET").upper()
    headers = DEFAULT_HEADER

    def _make_request(sess: requests.Session):
        """Внутренняя функция для выполнения запроса с замером времени."""
        try:
            start = monotonic()
            if method == "POST":
                resp = sess.request(
                    method, action, data=data, timeout=timeout, headers=headers
                )
            else:
                resp = sess.request(
                    method, action, params=data, timeout=timeout, headers=headers
                )
            elapsed = monotonic() - start

            body = resp.text or ""

            logger.debug(
                "Form request sent",
                extra={
                    "url": action,
                    "method": method,
                    "status": resp.status_code,
                    "body_len": len(body),
                    "time_sec": elapsed,
                },
            )

            return ResponseSnapshot(
                url=resp.url,
                status_code=resp.status_code,
                body=body,
                body_len=len(body),
                response_time=elapsed,
            )
        except requests.RequestException as e:
            logger.exception(
                "Request failed",
                extra={"url": action, "method": method, "error": str(e)},
            )
            return None

    if session is None:
        with requests.Session() as new_session:
            return _make_request(new_session)
    else:
        return _make_request(session)
