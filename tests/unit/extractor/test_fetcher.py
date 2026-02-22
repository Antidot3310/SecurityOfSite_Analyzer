import pytest
import requests
from src.extractor.fetcher import fetch_info


@pytest.fixture
def file_url(tmp_path):
    def _make(content, name):
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return f"file:///{p.as_posix()}"

    return _make


@pytest.mark.parametrize(
    "name, content, expected_len",
    [
        ("x.txt", "test", 4),
        ("a file.txt", "ok", 2),
    ],
)
def test_file_success(file_url, name, content, expected_len):
    url = file_url(content, name)
    r = fetch_info(url)
    assert r["ok"] is True
    assert r["status"] == 200
    assert r["length"] == expected_len


def test_file_not_found():
    r = fetch_info("file:///no/such/file.txt")
    assert not r["ok"]
    assert "File not found" in r["error"]


@pytest.mark.parametrize(
    "status, ok, length",
    [
        (200, True, 3),
        (404, False, None),
        (500, False, None),
    ],
)
def test_http_requests(monkeypatch, status, ok, length):

    class MockResponse:
        def __init__(self):
            self.status_code = status
            self.text = "abc" if status == 200 else ""

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(f"{self.status_code}")

    monkeypatch.setattr(
        "src.extractor.fetcher.requests.get", lambda *a, **k: MockResponse()
    )
    r = fetch_info("http://example.com")
    assert r["ok"] is ok
    if length is not None:
        assert r["length"] == length
