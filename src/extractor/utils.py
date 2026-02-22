"""
Модуль для работы с путями в URL и файловой системе.

функции:
    url_to_path  - преобразование file:// URL в системный путь

Поддерживаемые формы file URL:
    - file:///absolute/path
    - file://localhost/absolute/path
    - file:///C:/path
    - file://localhost/C:/path
    - file:relative/path
    - file:./relative/path
    - file:../relative/path
"""

import os
import posixpath
from urllib.parse import urlparse, unquote
from src.logger import get_logger

logger = get_logger(__name__)


def url_to_path(url: str) -> str:
    """
    Преобразует file URL в путь файловой системы.

    Параметры:
        url: строка вида file://... или file:...

    Возвращает:
        Путь, пригодный для использования.
    """
    parsed = urlparse(url)
    path = unquote(parsed.path)
    netloc = parsed.netloc.lower() if parsed.netloc else ""

    # Удаляем начальные двойные слеши
    while path.startswith("//"):
        path = path[1:]

    # Случай 1: относительный URL с netloc == '.'
    if netloc == ".":
        path = path.lstrip("/")
        return _format_relative_path(path)

    # Случай 2: нет netloc
    if not netloc:
        if path.startswith("/"):
            return _format_absolute_path(path)
        else:
            return _format_relative_path(path)

    # Случай 3: localhost
    if netloc == "localhost":
        return _format_absolute_path(path)

    raise ValueError(f"Unsupported file URL with netloc '{netloc}'.")


def _format_relative_path(path: str) -> str:
    """
    Форматирует относительный путь.
    """
    if not path:
        return "."

    if path.startswith(("./", "../")):
        return path
    return f"./{path}"


def _format_absolute_path(path: str) -> str:
    """
    Форматирует абсолютный путь, нормализует.
    """
    if os.name == "nt" and _is_windows_drive_path(path):
        path = path[1:]  
    return path


def _is_windows_drive_path(path: str) -> bool:
    """Проверяет, является ли путь Windows абсолютным с буквой диска в формате /X:/..."""
    return len(path) > 2 and path[0] == "/" and path[2] == ":" and path[1].isalpha()
