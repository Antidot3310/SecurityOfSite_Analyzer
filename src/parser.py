import os
import requests
from urllib.parse import urlparse


def fetch_info(url: str, timeout: int = 5) -> dict:
    result = {"url": url, "status": None, "length": None, "ok": False, "error": None}

    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()

        if scheme in ("http", "https"):
            resp = requests.get(
                url, timeout=timeout, headers={"User-Agent": "scanner-mvp/0.1"}
            )
            try:
                resp.raise_for_status()
                result.update(
                    {"status": resp.status_code, "length": len(resp.text), "ok": True}
                )
                return result
            except requests.exceptions.HTTPError as e:
                result.update(
                    {
                        "status": resp.status_code,
                        "length": len(resp.text),
                        "ok": False,
                        "error": str(e),
                    }
                )
                return result

        else:
            if scheme == "file":
                path = url[7:]  # remove 'file://'
            else:
                path = url
            if not os.path.exists(path):
                result.update({"error": "File not found"})

            with open(path, "r", encoding="UTF-8") as f:
                content = f.read()
                result.update({"status": 200, "length": len(content), "ok": True})
    except Exception as e:
        result.update
        ({"ok": False, "error": str(e)})
    return result
