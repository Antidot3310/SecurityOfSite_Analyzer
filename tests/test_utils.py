import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.utils import url_to_path, safe_urljoin


@pytest.mark.parametrize(
    "input_url,expected",
    [
        ("file://localhost/etc/passwd", "/etc/passwd"),
        ("file:./test.txt", "./test.txt"),
        ("file://./test.txt", "./test.txt"),
        ("file:test.txt", "./test.txt"),
        ("file:///path%20with%20spaces/file.txt", "/path with spaces/file.txt"),
        ("file:///test%23hash.txt", "/test#hash.txt"),
        ("file:////double//slashes", "/double//slashes"),
        ("file://///too/many", "/too/many"),
        ("file://", "."),
        ("file:", "."),
        ("file://./dir/subdir/file.txt", "./dir/subdir/file.txt"),
        ("file:relative.txt", "./relative.txt"),
        ("file:../parent.txt", "../parent.txt"),
    ],
)
def test_url_to_path_various(input_url, expected):
    assert url_to_path(input_url) == expected


@pytest.mark.parametrize(
    "base,url,expected",
    [
        ("https://a.com", "/p", "https://a.com/p"),
        ("https://a.com/", "p", "https://a.com/p"),
        ("", "/p", "/p"),
        (None, "/p", "/p"),
        ("https://a.com", None, "https://a.com"),
    ],
)
def test_safe_urljoin_variants(base, url, expected):
    assert safe_urljoin(base, url) == expected
