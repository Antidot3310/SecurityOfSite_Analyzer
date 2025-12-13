import os
import sys
from urllib.parse import quote
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.extractor.fetcher import fetch_info


def make_file(tmp_path, name="x.txt", content="test"):
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_file_success(tmp_path):
    p = make_file(tmp_path, "t.txt", "test")
    url = f"file://{p.as_posix()}"
    r = fetch_info(url)
    assert r["ok"] is True
    assert r["status"] == 200
    assert r["length"] == 4


def test_file_not_found():
    r = fetch_info("file:///no/such/file.txt")
    assert r["ok"] is False
    assert "File not found" in (r["error"] or "")


def test_file_with_spaces(tmp_path):
    p = make_file(tmp_path, "a file.txt", "ok")
    encoded = quote(p.as_posix())
    r = fetch_info(f"file:///{encoded}")
    assert r["ok"] is True
    assert r["length"] == 2


def test_http_success_and_http_error(monkeypatch):
    class Resp:
        def __init__(self, code, text):
            self.status_code = code
            self.text = text

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(f"{self.status_code}")

    # success
    monkeypatch.setattr(
        "src.extractor.fetcher.requests.get", lambda *a, **k: Resp(200, "abc")
    )
    r1 = fetch_info("http://example.com")
    assert r1["ok"] is True and r1["status"] == 200 and r1["length"] == 3

    # http error
    monkeypatch.setattr(
        "src.extractor.fetcher.requests.get", lambda *a, **k: Resp(404, "Not")
    )
    r2 = fetch_info("http://bad.example")
    assert r2["ok"] is False
    assert r2["status"] == 404 or "404" in (r2.get("error") or "")
