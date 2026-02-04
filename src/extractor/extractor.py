"""
Модуль предоставляет функционал для
получения html ресурса,
парсинга всех форм на ней

Функции:
    fetch_html() - получает html
    extrct_forms() - извлекает формы из страницы
        в виде списка объектов Form
"""

from typing import List, Optional
from bs4 import BeautifulSoup
from src.extractor.models import Form
from src.extractor.fetcher import fetch_info
from src.config import REQUEST_TIMEOUT
from src.logger import get_logger

logger = get_logger(__name__)


def fetch_html(url: str, timeout: int = REQUEST_TIMEOUT) -> Optional[str]:
    info = fetch_info(url=url, timeout=timeout)
    if info.get("ok"):
        return info.get("text")
    return None


def extract_forms(html: str, base_url: Optional[str]) -> List[Form]:
    """
    Маршализует все объекты типа form bs4
    в тип models.Form

    Параметры:
        html - html целевого ресурса
        base_url - url целевого ресурса
    """
    if not html:
        return []
    try:
        soup = BeautifulSoup(html, "html.parser")
        forms = [
            Form.from_soup_form(form_tag=f, base_url=base_url)
            for f in soup.find_all("form")
        ]
        logger.debug(
            "parsed forms", extra={"base_url": base_url, "forms_count": len(forms)}
        )
        if len(forms) == 0:
            logger.info("No forms found", extra={"base_url": base_url})
        return forms
    except Exception as e:
        logger.exception("Error extracting forms", extra={"error": str(e)})
        return []
