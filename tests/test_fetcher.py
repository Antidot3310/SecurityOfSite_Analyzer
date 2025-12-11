import os
import sys
from urllib.parse import quote

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.fetcher import fetch_info


# create temporary file for tests
def make_file(tmp_path, name="file.txt", content="test"):
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_file_success(tmp_path):
    p = make_file(tmp_path, "t.txt", "test")
    url = f"file:///{str(p).replace(os.sep, '/')}"
    res = fetch_info(url)
    assert res["ok"] and res["status"] == 200
    assert res["length"] == 4


def test_file_not_found():
    res = fetch_info("file:///non/existing/path.txt")
    assert not res["ok"]
    assert "File not found" in (res["error"] or "")


def test_http_success_and_empty(monkeypatch):
    class Resp:
        def __init__(self, code, text):
            self.status_code = code
            self.text = text

        def raise_for_status(self):
            return None

    monkeypatch.setattr("src.fetcher.requests.get", lambda *a, **k: Resp(200, "c"))
    r = fetch_info("http://example.com")
    assert r["ok"] and r["status"] == 200
    assert r["length"] == 1

    monkeypatch.setattr("src.fetcher.requests.get", lambda *a, **k: Resp(204, ""))
    r2 = fetch_info("http://example.com")
    assert r2["ok"]
    assert r2["length"] == 0


def test_invalid_url():
    r = fetch_info("not-a-valid-url")
    assert not r["ok"] and r["error"]


def test_file_with_spaces(tmp_path):
    p = make_file(tmp_path, "a file.txt", "ok")
    encoded = quote(str(p).replace(os.sep, "/"))
    r = fetch_info(f"file:///{encoded}")
    assert r["ok"]
