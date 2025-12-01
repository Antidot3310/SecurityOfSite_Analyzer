import sys
import os
import pytest

root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root not in sys.path:
    sys.path.insert(0, root)

from src.app import app
from src.storage.db import get_scan


def test_api_saves_scan(tmp_path, monkeypatch):
    sample = tmp_path / "s.html"
    sample.write_text(
        "<html><body><form><input name='a'></form></body></html>", encoding="utf-8"
    )
    client = app.test_client()
    resp = client.get(f"/api/parse?url=file://{sample}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "scan_id" in data
    scan_id = data["scan_id"]
    res = get_scan(scan_id=scan_id)
    assert res is not None
