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
