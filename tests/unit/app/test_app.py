import json
from unittest.mock import Mock, patch

from src.app import app, parse_forms_from_url, save_to_file


def test_save_to_file(tmp_path):
    p = tmp_path / "out.json"
    payload = [{"name": "form", "result": "x"}]
    save_to_file(payload, str(p))
    assert p.exists()
    assert json.loads(p.read_text(encoding="utf-8")) == payload


def test_parse_forms_from_url(monkeypatch):
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
