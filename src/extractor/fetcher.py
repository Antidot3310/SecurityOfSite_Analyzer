from urllib.parse import urlparse
from src.extractor.utils import url_to_path
import os
import requests
from typing import Optional, Any, Dict


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
    if not os.path.exists(path):
        return create_response(url=path, error="File not found")
    try:
        with open(path, "r", encoding="UTF-8") as f:
            content = f.read()
        return create_response(
            url=path, status=200, length=len(content), ok=True, text=content
        )
    except (IOError, OSError) as e:
        return create_response(url=path, error=f"File read error: {e}")


def fetch_web(url: str, timeout: int) -> Dict[str, Any]:
    try:
        resp = requests.get(
            url, timeout=timeout, headers={"User-Agent": "scanner-mvp/0.1"}
        )
        resp.raise_for_status()
        return create_response(
            url=url,
            status=resp.status_code,
            length=len(resp.text),
            ok=True,
            text=resp.text,
        )
    except requests.RequestException as e:
        return create_response(url=url, error=str(e))


def fetch_info(url: str, timeout: int = 5) -> Dict[str, Any]:
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
            return fetch_web("http://" + url, timeout)

        return create_response(url=url, error=f"Unsupported scheme: {scheme}")
    except Exception as e:
        return create_response(url=url, error=str(e))
