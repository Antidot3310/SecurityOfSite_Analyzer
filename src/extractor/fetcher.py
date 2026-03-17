"""
Модуль для отправки запросов к ресурсам по URL.

Поддерживаемые схемы:
    - http, https: веб-страницы
    - file: локальные файлы (URL вида file:///path/to/file)

Функции:
    fetch_info() - точка входа для получения содержимого по URL.
    fetch_local_file() - чтение локального файла.
    fetch_web() - загрузка данных с веб-ресурсов.
    create_response() - формирование ответа.
"""

import os
import requests
from typing import Optional, Any, Dict
from urllib.parse import urlparse
from src.extractor.utils import url_to_path
from src.config import REQUEST_TIMEOUT, DEFAULT_HEADER
from src.logger import get_logger

logger = get_logger(__name__)


class FetchResponse(dict):
    """
    Словарь ответа.

    url: исходный URL
    status: HTTP-статус
    length: длина содержимого в символах
    ok: флаг успешности операции
    error: описание ошибки (если есть)
    content: содержимое ресурса (если успешно)
    """

    url: str
    status: Optional[int]
    length: Optional[int]
    ok: bool
    error: Optional[str]
    content: Optional[str]


def create_response(
    url: str,
    status: Optional[int] = None,
    length: Optional[int] = None,
    ok: bool = False,
    error: Optional[str] = None,
    content: Optional[str] = None,
) -> FetchResponse:
    """
    Формирует словарь-ответ для всех функций модуля.

    Параметры:
        url: исходный URL
        status: HTTP-статус (или None для локальных файлов)
        length: длина содержимого
        ok: флаг успешности
        error: текст ошибки
        content: содержимое ресурса

    Возвращает:
        Словарь с описанными полями.
    """
    return {
        "url": url,
        "status": status,
        "length": length,
        "ok": ok,
        "error": error,
        "content": content,
    }


def fetch_local_file(file_path: str) -> Dict[str, Any]:
    """
    Обрабатывает запрос на локальный файл.

    Параметры:
        file_path: путь к файлу.

    Возвращает:
        Словарь-ответ (create_response).
    """
    if not os.path.exists(file_path):
        logger.warning("file not found", extra={"path": file_path})
        return create_response(url=file_path, error="File not found")
    try:
        with open(file_path, "r", encoding="UTF-8") as file:
            content = file.read()
            logger.debug(
                "fetched resource",
                extra={"url": file_path, "status": 200, "length": len(content)},
            )
        return create_response(
            url=file_path, status=200, length=len(content), ok=True, content=content
        )
    except (IOError, OSError) as e:
        logger.warning("File read error", extra={"path": file_path, "error": str(e)})
        return create_response(url=file_path, error=f"File read error: {e}")


def fetch_web(url: str, session: requests.Session) -> FetchResponse:
    """
    Обрабатывает  запросы на веб ресурсам.

    Параметры:
        url: URL целевого ресурса
        session: текущая сессия (для правильной аутентификации)

    Возвращает:
        Словарь-ответ (create_response).
    """
    try:
        if (session == None):
            logger.error("No session for web", extra={"url": url})
            return create_response(url=url, status=None)
        resp = session.get(
            url,
            allow_redirects=True
        )
        resp.raise_for_status()

        return create_response(
            url=url,
            status=resp.status_code,
            length=len(resp.text),
            ok=True,
            content=resp.text,
        )
    except requests.HTTPError() as e:
        logger.warning(
            "Web request failed", extra={"url": url, "error": str(e)}
        )
        return create_response(url=url, status=None, error=str(e))


def fetch_info(url: str, session: Optional[requests.Session] = None) -> FetchResponse:
    """
    Отправляет запрос к целевому ресурсу и возвращает результат.

    Параметры:
        url: URL целевого ресурса
        session: текущая сессия (для правильной аутентификации)

    Возвращает:
        Словарь-ответ (create_response).
    """
    if not url or not url.strip():
        logger.warning("Empty URL provided")
        return create_response(url=url, error="Empty URL")

    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()

        if scheme in ("http", "https"):
            return fetch_web(url, session)

        if scheme == "file":
            path = url_to_path(url)
            return fetch_local_file(path)

        if not scheme:
            tried_url = "http://" + url
            logger.warning(
                "trying http fallback", extra={"original": url, "tried": tried_url}
            )
            return fetch_web(tried_url, session)

    except Exception as e:
        logger.exception(
            "Unexpected error in fetch_info", extra={"url": url, "error": str(e)}
        )
        return create_response(url=url, error=str(e))
