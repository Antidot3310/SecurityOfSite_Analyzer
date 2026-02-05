"""
Модуль предоставляет абстракции реальных обьектов
уязвимость (целевого ресурса) и запрос (response)
в виде классов, а ткаже функции для работы с ними

Классы:
    Finding - класс абстракция уязвимости
    ResponseSnapshot - класс абстракция запроса

Функции:
    build_base_line() - создает базовый запрос к форме
    build_test_data() - создает запрос к форме с payload
    send_form_request() - отправляет запрос и обрабатывает его
"""

import requests
from typing import List, Optional, Any
from dataclasses import dataclass, asdict
from time import monotonic
from .types import Payload
from src.config import REQUEST_TIMEOUT
from src.logger import get_logger

logger = get_logger(__name__)

BODY_PREVIEW = 512


@dataclass
class Finding:
    form_index: Optional[Any]
    field_name: str
    # error code, pattern in response, time delay, etc.
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
            "payload": (self.payload.to_dict()),
            "response_time_ms": self.response_time_ms,
            "body_len": self.body_len,
            "url": self.url,
        }


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
    # Подстановка payload в заданное поле
    name = input_field.get("name")
    if name:
        d[name] = payload.payload
    return d


def build_base_line(inputs: List[dict]) -> dict:
    # create base response body
    return {inp["name"]: inp.get("value", "") for inp in inputs if inp.get("name")}


def send_form_request(
    form: dict,
    data: dict,
    timeout: int = REQUEST_TIMEOUT,
    session: Optional[requests.Session] = None,
) -> Optional[ResponseSnapshot]:
    action = form.get("action")
    if not action:
        print(f"Form has no action attribute: {form.get("form_id")}")
        return None

    method = (form.get("method") or "GET").upper()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0"
    }

    def _make_request(s: requests.Session):
        """
        Отправляет запрос, получает ответ,
        рассчитывает его время, возвращает ResponseSnapshot"""
        try:
            start = monotonic()
            resp = s.request(
                method,
                action,
                params=None if method == "POST" else data,
                data=data if method == "POST" else None,
                timeout=timeout,
                headers=headers,
            )
            elapsed_ms = (monotonic() - start) * 1000
        except requests.RequestException as e:
            print(f"Request failed for: {action}, {e}")
            return None
        return ResponseSnapshot(
            # Url, если существует, иначе action
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
