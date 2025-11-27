import requests
from urllib.parse import urlparse
import os


def fetch_info(url: str, timeout: int) -> dict:
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


def main():

    sources = [
        # "https://httpbin.org/get",
        "file://./src/ex2.html",
        # "https://chat.deepseek.com/a/chat/s/839531b0-44ff-48c8-810e-42560871fa6a",
        # "https://www.youtube.com/",
    ]
    for url in sources:
        info = fetch_info(url, 4)
        print(info)


if __name__ == "__main__":
    main()
