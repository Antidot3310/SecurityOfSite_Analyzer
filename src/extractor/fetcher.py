"""
Модулю предоставляет главным образом функцию
берущую логику отправки и обработки запроса на url адрес

Функции:
    create_response() - маршализует запрос в удобный словарь
    fetch_local_file() - логика обработки для локальных файлов
    fetch_web() - логика обработки для веб сервисов
    fetch_info() - выполняет логику отправки и обработки запроса (возлагает ее на fetch_local_file() и detch_web())
"""

import os
import requests
from typing import Optional, Any, Dict
from urllib.parse import urlparse
from src.extractor.utils import url_to_path
from src.config import REQUEST_TIMEOUT
from src.logger import get_logger

logger = get_logger(__name__)


def create_response(
    url: str,
    status: Optional[int] = None,
    length: Optional[int] = None,
    ok: bool = False,
    error: Optional[str] = None,
    text: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "url": url,
        "status": status,
        "length": length,
        "ok": ok,
        "error": error,
        "text": text,
    }


def fetch_local_file(path: str) -> Dict[str, Any]:
    """
    Обрабатывает запрос на локальный файл

    Параметр: path - путь к файлу
    """
    if not os.path.exists(path):
        logger.warning("file not found", extra={"path": path})
        return create_response(url=path, error="File not found")
    try:
        with open(path, "r", encoding="UTF-8") as file:
            content = file.read()
            # логирование успешного запроса
            logger.debug(
                "fetched resource",
                extra={"url": path, "status": 200, "length": len(content)},
            )
        return create_response(
            url=path, status=200, length=len(content), ok=True, text=content
        )
    except (IOError, OSError) as e:
        return create_response(url=path, error=f"File read error: {e}")


def fetch_web(url: str, timeout: int) -> Dict[str, Any]:
    """
    Обрабатывает  запросы на web сервисы

    Параметры:
        url - url целевого сайта
        timeout - максимальное время ожидания ответа от сервера
    """
    try:
        # Имитация запроса от пользователя
        resp = requests.get(
            url,
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0"
            },
        )
        resp.raise_for_status()
        # логирование успешного запроса
        logger.debug(
            "fetched resource",
            extra={"url": url, "status": resp.status_code, "length": len(resp.text)},
        )
        return create_response(
            url=url,
            status=resp.status_code,
            length=len(resp.text),
            ok=True,
            text=resp.text,
        )
    except requests.RequestException as e:
        return create_response(url=url, status=resp.status_code, error=str(e))


def fetch_info(url: str, timeout: int = REQUEST_TIMEOUT) -> Dict[str, Any]:
    """
    Отправляет, принимает и предоставляет в удобной форме
    запрос на целевой ресурс

    Параметры:
        url - url целевого ресурса
        timeout - максимальное время ожидания ответа от ресурса (для web)
    """
    try:
        parsed = urlparse(url)
        scheme = (parsed.scheme or "").lower()

        if scheme in ("http", "https"):
            return fetch_web(url, timeout)

        if scheme == "file":
            path = url_to_path(url)
            return fetch_local_file(path)

        # try http
        if not scheme:
            tried_url = "http://" + url
            logger.debug(
                "trying http fallback", extra={"original": url, "tried": tried_url}
            )
            return fetch_web(tried_url, timeout)

        return create_response(url=url, error=f"Unsupported scheme: {scheme}")
    except Exception as e:
        logger.exception("fetch error", extra={"url": url})
        return create_response(url=url, error=str(e))
