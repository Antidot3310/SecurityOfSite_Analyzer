import pytest
from src.extractor.extractor import extract_forms


@pytest.mark.parametrize(
    "html, base_url, expected_action, expected_method, expected_enctype, expected_form_id",
    [
        (
            '<form action="/path"><input name="x"></form>',
            "https://host",
            "https://host/path",
            "get",
            None,
            None,
        ),
        (
            '<form action="rel"><input name="x"></form>',
            "https://host/base/",
            "https://host/base/rel",
            "get",
            None,
            None,
        ),
        (
            '<form method="post"><input name="x"></form>',
            "url",
            None,
            "post",
            None,
            None,
        ),
        ('<form><input name="x"></form>', "url", None, "get", None, None),
        (
            '<form id="f" class="a b" enctype="multipart/form-data"><input name="x"></form>',
            "",
            None,
            "get",
            "multipart/form-data",
            "f",
        ),
    ],
)
def test_form_attributes(
    html, base_url, expected_action, expected_method, expected_enctype, expected_form_id
):
    forms = extract_forms(html, base_url)
    assert len(forms) == 1
    f = forms[0]
    if expected_action is not None:
        assert f.action == expected_action
    if expected_method is not None:
        assert f.method == expected_method
    if expected_enctype is not None:
        assert f.enctype == expected_enctype
    if expected_form_id is not None:
        assert f.form_id == expected_form_id


def test_empty_html():
    assert extract_forms("", "url") == None


def test_no_forms():
    html = "<div></div>"
    assert extract_forms(html, "url") == []
