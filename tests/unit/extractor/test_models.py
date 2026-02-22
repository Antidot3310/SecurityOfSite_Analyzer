from bs4 import BeautifulSoup
from src.extractor.models import InputField, Form


def test_field_factories():
    test_html = (
        '<input name="u" type="text" value="john" required placeholder="p">'
        '<textarea name="b">txt</textarea>'
    )
    soup = BeautifulSoup(test_html, "html.parser")

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


def test_from_soup_form():
    html = '<form id="f" class="c1 c2" action="/go" method="POST" enctype="multipart/form-data"><input name="x"></form>'
    form_tag = BeautifulSoup(html, "html.parser").find("form")

    frm = Form.from_soup_form(form_tag, "https://ex.com")
    d = frm.to_dict()

    assert frm.form_id == "f"
    assert frm.action == "https://ex.com/go"
    assert frm.method == "post"
    assert isinstance(d["inputs"], list) and d["inputs"][0]["name"] == "x"
