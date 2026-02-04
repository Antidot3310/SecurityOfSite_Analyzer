import pytest
from src.extractor.utils import url_to_path, safe_urljoin


@pytest.mark.parametrize(
    "url,excepted",
    [
        # Относительные пути с netloc == "."
        ("file://.", "."),
        ("file://./", "."),
        ("file://./../x", "../x"),
        ("file://./x/y", "./x/y"),
        # Относительные пути без netloc
        ("file:x", "./x"),
        ("file:../x", "../x"),
        ("file:./x/y", "./x/y"),
        # Абсолютные пути Windows (с локальным хостом)
        ("file:///C:/Windows/System32", "C:/Windows/System32"),
        ("file://localhost/C:/Users/Name", "C:/Users/Name"),
        ("file:///D:/folder/file.txt", "D:/folder/file.txt"),
        # Пути с двойными слешами
        ("file:////home/user", "/home/user"),
        ("file://///home/user", "/home/user"),
        # Специальные символы в URL
        ("file:///path%20with%20spaces", "/path with spaces"),
        ("file:///path%2Fwith%2Fencoded", "/path/with/encoded"),
        ("file:///%D0%BF%D1%83%D1%82%D1%8C", "/путь"),  # кириллица
    ],
)
def test_various_url_to_path(url, excepted):
    assert url_to_path(url) == excepted


@pytest.mark.parametrize(
    "base,url,expected",
    [
        ("https://a.com", "/p", "https://a.com/p"),
        ("https://a.com/", "p", "https://a.com/p"),
        ("", "/p", "/p"),
        (None, "/p", "/p"),
    ],
)
def test_safe_urljoin_variants(base, url, expected):
    assert safe_urljoin(base, url) == expected
