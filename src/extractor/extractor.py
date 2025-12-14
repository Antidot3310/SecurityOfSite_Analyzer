from typing import List, Optional
from bs4 import BeautifulSoup
from src.extractor.models import Form
from src.extractor.fetcher import fetch_info


def fetch_html(url: str, timeout: int = 10) -> Optional[str]:
    info = fetch_info(url=url, timeout=timeout)
    if info.get("ok"):
        return info.get("text")
    return None


def extract_forms(html: str, base_url: Optional[str]) -> List[Form]:
    if not html:
        return []
    try:
        soup = BeautifulSoup(html, "html.parser")
        return [Form.from_soup_form(form_tag=f, base_url=base_url) for f in soup.find_all("form")]
    except Exception as e:
        print(f"Error extracting forms: {e}")
        return []
