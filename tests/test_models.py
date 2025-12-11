import os
import sys
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.models import InputField, Form, parse_form_inputs


def test_inputfield_factories():
    s = BeautifulSoup(
        '<input name="u" type="text" value="john" required placeholder="p">'
        '<textarea name="b">txt</textarea>'
        '<select name="c"><option value="1" selected>1</option></select>',
        "html.parser",
    )
    inp = s.find("input")
    ta = s.find("textarea")
    sel = s.find("select")

    f1 = InputField.from_input_tag(inp)
    assert (f1.name, f1.field_type, f1.value, f1.required) == (
        "u",
        "text",
        "john",
        True,
    )

    f2 = InputField.from_textarea_tag(ta)
    assert (f2.name, f2.field_type, f2.value) == ("b", "textarea", "txt")

    f3 = InputField.from_select_tag(sel)
    assert f3.name == "c" and f3.value[0]["value"] == "1"


def test_form_from_soup_and_dict():
    html = '<form id="f" class="c1 c2" action="/go" method="POST" enctype="multipart/form-data"><input name="x"></form>'
    form = BeautifulSoup(html, "html.parser").find("form")
    obj = Form.from_soup_form(form, "https://ex.com")
    d = obj.to_dict()
    assert obj.form_id == "f"
    assert obj.classes == ["c1", "c2"]
    assert obj.action == "https://ex.com/go"
    assert d["inputs"][0]["name"] == "x"


def test_form_no_action_uses_base_url():
    form_tag = BeautifulSoup(
        '<form method="POST"><input name="t"></form>', "html.parser"
    ).find("form")
    obj = Form.from_soup_form(form_tag, "https://ex.com/page")
    assert obj.action == "https://ex.com/page"
    assert obj.method == "post"
