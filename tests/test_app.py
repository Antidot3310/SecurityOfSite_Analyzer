from src.app import app


def test_api_parse_local(tmp_path):
    sample = tmp_path / "t.html"
    sample.write_text(
        "<html><body><form><input name='a'></form></body></html>", encoding="utf-8"
    )
    client = app.test_client()
    resp = client.get(f"/api/parse?url={sample.as_uri()}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "forms" in data
    assert data["count"] == 1

