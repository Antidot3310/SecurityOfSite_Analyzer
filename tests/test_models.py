import os
import sys
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.extractor.models import InputField, Form


def test_inputfield_factories_and_select():
    html = (
        '<input name="u" type="text" value="john" required placeholder="p">'
        '<textarea name="b">txt</textarea>'
        '<select name="c"><option value="1" selected>1</option></select>'
    )
    soup = BeautifulSoup(html, "html.parser")

    f_input = InputField.from_input_tag(soup.find("input"))
    assert (f_input.name, f_input.field_type, f_input.value, f_input.required) == (
        "u",
        "text",
        "john",
        True,
    )

    f_textarea = InputField.from_textarea_tag(soup.find("textarea"))
    assert (f_textarea.name, f_textarea.field_type, f_textarea.value) == (
        "b",
        "textarea",
        "txt",
    )

    f_selected = InputField.from_select_tag(soup.find("select"))
    assert (
        f_selected.name == "c"
        and isinstance(f_selected.value, list)
        and f_selected.value[0]["value"] == "1"
    )


def test_form_from_soup_form_and_defaults():
    html = '<form id="f" class="c1 c2" action="/go" method="POST" enctype="multipart/form-data"><input name="x"></form>'
    form_tag = BeautifulSoup(html, "html.parser").find("form")

    frm = Form.from_soup_form(form_tag, "https://ex.com")
    d = frm.to_dict()

    assert frm.form_id == "f"
    assert frm.classes == ["c1", "c2"]
    assert frm.action == "https://ex.com/go"
    assert frm.method == "post"
    assert isinstance(d["inputs"], list) and d["inputs"][0]["name"] == "x"
