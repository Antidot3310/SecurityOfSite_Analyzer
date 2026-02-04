"""
Модуль предоставляет служебный функции работы с путями

Предоставляет функции:
    safe_urljoin (безопасный wrap),
    url_to_path (преобразование вводимого пути в валидный)
"""

import os
from typing import Optional
from urllib.parse import urlparse, unquote, urljoin


def safe_urljoin(base: Optional[str], url: str) -> str:
    """
    Безопасное обработка base = None.

    Параметры:
        base - абсолютный url
        url - относительный url
    """
    if not base:
        return url
    return urljoin(base, url)


def url_to_path(url: str) -> str:
    """
    Преобразует url с схемой "file" в валидный файловый путь
    """
    parsed = urlparse(url)
    path = unquote(parsed.path)
    netloc = (parsed.netloc or "").lower()

    # Срезаем лишние слеши
    while path.startswith("//"):
        path = path[1:]

    # Обработка относительных путей
    if _is_relative_path_case(netloc, path):
        return _handle_relative_path(netloc, path)

    # Обработка localhost и пустого netloc
    if _is_localhost_case(netloc):
        return _handle_localhost_path(path)

    # Общий случай: netloc + path
    return f"{netloc}{path}"


def _is_relative_path_case(netloc: str, path: str) -> bool:
    return netloc == "." or (not netloc and not path.startswith("/"))


def _handle_relative_path(netloc: str, path: str) -> str:
    path = path.lstrip("/")

    if netloc == ".":
        if not path:
            return "."
        if path.startswith(("./", "../")):
            return path
        return f"./{path}"

    # Случай без netloc и без ведущего слеша
    if path.startswith(("./", "../")):
        return path
    return f"./{path}" if path else "."


def _is_localhost_case(netloc: str) -> bool:
    return not netloc or netloc == "localhost"


def _handle_localhost_path(path: str) -> str:
    if os.name == "nt" and _is_windows_absolute_path(path):
        return path[1:]  # Убираем ведущий слеш для Windows путей
    return path


def _is_windows_absolute_path(path: str) -> bool:
    return (
        len(path) > 2 and path.startswith("/") and path[1].isalpha() and path[2] == ":"
    )
