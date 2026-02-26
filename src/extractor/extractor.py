"""
Модуль предоставляет функционал для
получения html кода ресурса,
парсинга всех форм на нем.

Функции:
    fetch_html() - получает html
    extract_forms() - извлекает формы из страницы в виде списка объектов Form
"""

from typing import List, Optional
from bs4 import BeautifulSoup
from src.extractor.models import Form
from src.extractor.fetcher import fetch_info
from src.extractor.render import render_html_with_playwright
from src.logger import get_logger

logger = get_logger(__name__)


def fetch_html(url: str) -> Optional[str]:
    """
    Получает HTML-код страницы по указанному URL.

    Параметры:
        url: адрес страницы

    Возвращает:
        HTML-код в виде строки или None, если запрос не удался.
    """
    rendered = render_html_with_playwright(url)
    if rendered:
        return rendered
    
    info = fetch_info(url)
    if info.get("ok"):
        return info.get("content")
    return None


def extract_forms(html: str, url: str) -> Optional[List[Form]]:
    """
    Извлекает все формы из HTML-кода страницы.

    Параметры:
        html - html-код страницы
        url - url страницы (используется для построения абсолютных ссылок)

    Возвращает:
        Список объектов Form. Если HTML пуст или произошла ошибка парсинга,
        возвращается None.
    """
    if not html:
        logger.warning("Empty HTML in extractor", extra={"url": url})
        return None
    try:
        soup = BeautifulSoup(html, "html.parser")
        page_js_hint = page_has_js(soup)
        forms = [
            Form.from_soup_form(form_tag=f, url=url, page_js_hint=page_js_hint)
            for f in soup.find_all("form")
        ]
        return forms
    except Exception as e:
        logger.exception("Error extracting forms", extra={"url": url, "error": str(e)})
        return None


def get_forms(url: str) -> Optional[List[Form]]:
    """
    Получает HTML по URL и извлекает из него формы.

    Параметры:
        url: адрес страницы

    Возвращает:
        Список объектов Form. Если HTML не удалось получить или произошла ошибка,
        возвращается None.
    """
    html = fetch_html(url)
    if html is None:
        logger.warning("Cannot fetch HTML", extra={"url": url})
        return None
    return extract_forms(html, url)


def page_has_js(soup) -> bool:
    return bool(soup.find_all("script"))
