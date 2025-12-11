from src.fetcher import url_to_path
from src.models import Form, InputField
from src.utils import url_to_path
from urllib.parse import urlparse
from typing import List, Optional
from bs4 import BeautifulSoup
import requests
from pathlib import Path


def read_html_file(file_path: str) -> Optional[str]:
    try:
        path = Path(file_path)
        if not path.exists():
            return None
        with open(path, "r", encoding="UTF-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error during reading html from local file: {str(e)}")
        return None


def read_html_web(url: str, timeout: int) -> Optional[str]:
    try:
        response = requests.get(
            url, timeout=timeout, headers={"User-Agent": "MVP-Scanner 0.1"}
        )
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error during reading html from web: {str(e)}")
        return None


def fetch_html(url: str, timeout: int = 10) -> Optional[str]:
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()

    if not urlparse(url).scheme:
        scheme = "http://" + url

    if scheme == "file":
        path = url_to_path(url)
        return read_html_file(path)

    else:
        return read_html_web(url, timeout)


def extract_forms(html: str, url: Optional[str]) -> List[Form]:
    if not html:
        return []
    try:
        soup = BeautifulSoup(html, "lxml")
        return [Form.from_soup_form(form, url) for form in soup.find_all("form")]
    except Exception as e:
        print(f"Error during extracting forms from html: {str(e)}")
        return []
