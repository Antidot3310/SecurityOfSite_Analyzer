import os
import sys
import json
import tempfile
from unittest.mock import Mock, patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.app import app
from src.storage.db import init_db, get_scan


def test_complete_flask_workflow_minimal(tmp_path):
    db_fd = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db_fd.name
    db_fd.close()

    test_html = """
    <html><body>
      <form id="login" action="/login" method="post"><input name="u"/></form>
      <form id="search" action="/search" method="get"><input name="q"/></form>
    </body></html>
    """

    mock_form1 = Mock()
    mock_form1.to_dict.return_value = {
        "form_id": "login",
        "method": "post",
        "inputs": [{"name": "u"}],
    }
    mock_form2 = Mock()
    mock_form2.to_dict.return_value = {
        "form_id": "search",
        "method": "get",
        "inputs": [{"name": "q"}],
    }

    try:
        with patch("src.app.fetch_html", return_value=test_html) as m_fetch, patch(
            "src.app.extract_forms", return_value=[mock_form1, mock_form2]
        ) as m_extract, patch("src.app.save_to_file") as m_save_file, patch(
            "src.storage.db.DEFAULT_DB_PATH", db_path
        ):
            init_db(db_path)
            with app.test_client() as client:
                url = "https://example.com/page"
                resp = client.get(f"/api/parse?url={url}")
                assert resp.status_code == 200, resp.data.decode("utf-8")
                data = json.loads(resp.data)
                assert data["count"] == 2
                assert isinstance(data["scan_id"], int)
                assert len(data["forms"]) == 2
                m_fetch.assert_called_once_with(url)
                # запись в БД
                rec = get_scan(data["scan_id"], db_path)
                assert rec is not None and rec["target"] == url and rec["count"] == 2
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
