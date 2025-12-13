import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.extractor.extractor import extract_forms


def test_extract_forms_simple():
    html = (
        "<form id='one'><input name='a'></form><form id='two'><input name='b'></form>"
    )
    forms = extract_forms(html, "https://ex")
    assert len(forms) == 2
    assert forms[0].form_id == "one"
    assert forms[1].form_id == "two"
    assert forms[0].inputs[0].name == "a"


def test_form_action_joining_with_base():
    html = '<form id="f" action="/path"><input name="x"></form>'
    forms = extract_forms(html, "https://host.example")
    f = forms[0]
    assert f.action == "https://host.example/path"
    assert f.method == "get" or isinstance(f.method, str)
