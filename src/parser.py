import os
import requests
from urllib.parse import urlparse, unquote
from typing import Optional, Any


def url_to_path(url: str) -> str:
    parsed = urlparse(url)
    # decode %xx escapse
    path = unquote(parsed.path)

    while path.startswith("//"):
        path = path[1:]

    # process relative pathes
    if parsed.netloc == ".":
        return f".{path}" if path.startswith("/") else f"./{path}"

    # process windows pathes
    if os.name == "nt" and path.startswith("/") and len(path) > 2 and path[2] == ":":
        # /C:/Users/... -> C:/Users/...
        path = path[1:]

    return path


# create structure to write response result
def create_response(
    url: str,
    status: Optional[int] = None,
    length: Optional[int] = None,
    ok: bool = False,
    error: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "url": url,
        "status": status,
        "length": length,
        "ok": ok,
        "error": error,
    }


def fetch_local_file(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        return create_response(url=path, error="File not found")
    try:
        with open(path, "r", encoding="UTF-8") as f:
            content = f.read()
            return create_response(url=path, status=200, length=len(content), ok=True)
    except (IOError, OSError) as e:
        return create_response(path, error=f"File read error: {str(e)}")


def fetch_web(url: str, timeout: int) -> dict[str, Any]:
    try:
        resp = requests.get(
            url, timeout=timeout, headers={"User-Agent": "scanner-mvp/0.1"}
        )
        resp.raise_for_status()
        return create_response(
            url=url, status=resp.status_code, length=len(resp.text), ok=True
        )
    except requests.exceptions.HTTPError as e:
        return create_response(url=url, error=str(e))


def fetch_info(url: str, timeout: int = 5) -> dict[str, Any]:
    # result = {"url": str, "status": int, "length": int, "ok": bool, "error": str}
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()

        if scheme in ("http", "https"):
            return fetch_web(url, timeout)

        elif scheme == "file":
            path = url_to_path(url)
            return fetch_local_file(path)
    except Exception as e:
        return create_response(url=url, error=str(e))
