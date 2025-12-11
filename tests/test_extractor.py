import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.extractor import (
    extract_forms,
    read_html_file,
    read_html_web,
)


def test_extract_forms_and_empty():
    html = "<form id='one'></form><form id='two'></form>"
    forms = extract_forms(html, "https://ex")
    assert len(forms) == 2 and forms[0].form_id == "one"
    assert extract_forms("", "https://ex") == []
    assert extract_forms(None, "https://ex") == []


def test_read_html_file_success_and_not_found(tmp_path):
    p = tmp_path / "a.html"
    p.write_text("<p>ok</p>", encoding="utf-8")
    assert read_html_file(str(p)) == "<p>ok</p>"
    assert read_html_file("/non/existent/file.html") is None


def test_read_html_web_success_and_error(monkeypatch):
    class R:
        def __init__(self, code, text):
            self.status_code = code
            self.text = text

        def raise_for_status(self):
            return None

    monkeypatch.setattr(
        "src.extractor.requests.get", lambda *a, **k: R(200, "<html>ok</html>")
    )
    assert read_html_web("https://ex", timeout=5) == "<html>ok</html>"

    def bad_get(*a, **k):
        r = R(500, "")

        def raise_err():
            raise Exception("500")

        r.raise_for_status = raise_err
        return r

    monkeypatch.setattr("src.extractor.requests.get", bad_get)
    assert read_html_web("https://ex", timeout=5) is None


def test_integration_form_extraction_full():
    html = """
    <form id="login" action="/login" method="POST">
      <input type="text" name="username" required>
      <input type="password" name="password">
      <textarea name="c"></textarea>
      <select name="role"><option value="u">u</option><option value="a" selected>a</option></select>
      <button type="submit">Go</button>
    </form>
    <form id="s"><input type="search" name="q"></form>
    """
    forms = extract_forms(html, "https://ex")
    assert len(forms) == 2
    a = forms[0]
    assert a.form_id == "login"
    assert a.action == "https://ex/login"
    assert a.method == "post"
    assert len(a.inputs) == 4
    assert a.inputs[3].field_type == "select" and a.inputs[3].value[1]["selected"]
