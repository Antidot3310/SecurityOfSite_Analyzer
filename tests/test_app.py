import os
import sys
import json
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.app import app, parse_forms_from_url, save_to_file


def test_save_to_file_and_unicode(tmp_path):
    p = tmp_path / "out.json"
    payload = [{"name": "form", "result": "x"}]
    save_to_file(payload, str(p))
    assert p.exists()
    assert json.loads(p.read_text(encoding="utf-8")) == payload


def test_parse_forms_from_url_success(monkeypatch):
    html = "<html><form></form><form></form></html>"
    monkeypatch.setattr("src.app.fetch_html", lambda u: html)
    monkeypatch.setattr(
        "src.app.extract_forms",
        lambda html, url: [
            Mock(to_dict=lambda: {"id": "a"}),
            Mock(to_dict=lambda: {"id": "b"}),
        ],
    )
    res = parse_forms_from_url("http://ex")
    assert res["forms_count"] == 2 and res["html_length"] == len(html)


def test_api_parse_missing_url():
    with app.test_client() as c:
        r = c.get("/api/parse")
        assert r.status_code == 400
        assert "missing url parameter" in json.loads(r.data)["error"]


def test_api_parse_success_and_calls():
    html = "<html><form id='t'></form></html>"
    with patch("src.app.fetch_html", return_value=html), patch(
        "src.app.extract_forms"
    ) as m_extract, patch("src.app.save_scan", return_value=42), patch(
        "src.app.save_to_file"
    ):
        m_extract.return_value = [Mock(to_dict=lambda: {"id": "form1", "inputs": []})]
        with app.test_client() as c:
            r = c.get("/api/parse?url=http://example.com")
            assert r.status_code == 200
            j = json.loads(r.data)
            assert j["scan_id"] == 42 and j["count"] == 1


def test_full_integration_file_url(tmp_path):
    content = "<form action='/a'><input name='x'></form><form action='/b'></form>"
    p = tmp_path / "page.html"
    p.write_text(content, encoding="utf-8")
    url = (
        f"file:///{str(p).replace(os.sep, '/')}"
        if os.name == "nt"
        else f"file://{str(p)}"
    )
    with patch("src.app.save_scan", return_value=100), patch("src.app.save_to_file"):
        with app.test_client() as c:
            r = c.get(f"/api/parse?url={url}")
            assert r.status_code == 200
            j = json.loads(r.data)
            assert j["count"] == 2 and j["scan_id"] == 100
