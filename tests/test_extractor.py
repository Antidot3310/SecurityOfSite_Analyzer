import pytest
import os
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root not in sys.path:
    sys.path.insert(0, root)
from src.extractor import *


def test_fetch_html_local_sample():
    local_html = root + "/src/local.html"
    html = fetch_html(f"file://{local_html}")
    assert html is not None
    assert "<form" in html


def test_extract_forms_sample():
    local_html = root + "/src/local.html"
    html = fetch_html(f"file://{local_html}")
    forms = extract_forms(html)
    assert isinstance(forms, list)

    first = forms[0]
    assert hasattr(first, "action")
    assert hasattr(first, "method")
    assert hasattr(first, "inputs")
    assert isinstance(first.inputs, list)


def test_select_options():
    html = """
    <form action="/submit" method="post">
        <select name="choices" multiple>
            <option value="1" selected>Option 1</option>
            <option value="2">Option 2</option>
            <option value="3" selected>Option 3</option>
        </select>
    </form>
    """
    forms = extract_forms(html)
    select_field = forms[0].inputs[0]
    assert select_field.name == "choices"
    assert select_field.field_type == "select"
    assert select_field.meta["multiple"] is True
    options = select_field.value
    assert len(options) == 3
    assert options[0]["value"] == "1"
    assert options[0]["selected"] is True
    assert options[1]["value"] == "2"
    assert options[1]["selected"] is False
    assert options[2]["value"] == "3"
    assert options[2]["selected"] is True


def test_textarea_and_placeholder():
    html = """
    <form action="/submit" method="post">
        <textarea name="comments" placeholder="Enter your comments here" required></textarea>
    </form>
    """
    forms = extract_forms(html)
    textarea_field = forms[0].inputs[0]
    assert textarea_field.name == "comments"
    assert textarea_field.field_type == "textarea"
    assert textarea_field.placeholder == "Enter your comments here"
    assert textarea_field.required is True


def test_missing_input_name():
    html = """
    <form action="/submit" method="post">
        <input type="text" value="No name attribute">
    </form>
    """
    forms = extract_forms(html)
    input_field = forms[0].inputs[0]
    assert input_field.name is None
    assert input_field.field_type == "text"
    assert input_field.value == "No name attribute"
