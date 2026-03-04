"""
Модуль аутентификации в DVWA.

Функции:
    try_login_dvwa() - производит попытку аутентифицироваться в DVWA.
"""

import requests
from urllib.parse import urljoin
from typing import Optional

from src.logger import get_logger
from src.extractor.models import Form
from src.extractor.extractor import extract_forms
from src.config import (
    DEFAULT_HEADER,
    LOGIN_PATH,
    SECURITY_COOKIE_NAME,
    SECURITY_COOKIE_VALUE,
    LOGIN_FORM_FIELDS,
    LOGIN_BUTTON_VALUE,
    LOGIN_BUTTON_NAME,
    VERIFICATION_FAILURE_INDICATORS,
)

logger = get_logger(__name__)


def try_login_dvwa(
    session: requests.Session,
    target_url: str,
    username: str = "admin",
    password: str = "password",
    timeout: int = 8,
) -> bool:
    """
    Выполняет попытку входа в DVWA с указанными учётными данными.

    Последовательность действий:
      1. Устанавливает cookie security=low для переключения DVWA в низкий уровень безопасности.
      2. Запрашивает страницу /login.php для получения CSRF-токена (user_token).
      3. Извлекает форму входа и заполняет её поля.
      4. Отправляет POST-запрос с данными для входа.
      5. Проверяет успешность входа, запрашивая целевой URL.

    Args:
        session: Сессия requests, в которой будет выполняться вход.
        target_url: Базовый URL целевого приложения (например, http://localhost/dvwa/).
        username: Имя пользователя для входа.
        password: Пароль.
        timeout: Таймаут для HTTP-запросов в секундах.

    """
    try:
        login_url = urljoin(target_url, LOGIN_PATH)

        set_security_cookie(session)
        login_page_response = fetch_login_page(session, login_url, timeout)
        if login_page_response is None:
            return False

        login_form = extract_login_form(login_page_response.text, login_url)
        if login_form is None:
            return False

        payload = build_login_payload(login_form, username, password)
        submit_login_form(session, login_form.action, payload, timeout)

        return verify_login_success(session, target_url, timeout)

    except Exception as e:
        logger.exception(
            "Unexpected error during DVWA login attempt",
            extra={"target_url": target_url, "error": str(e)},
        )
        return False


def set_security_cookie(session: requests.Session) -> None:
    """Устанавливает cookie security=low для переключения DVWA в низкий уровень безопасности."""
    try:
        session.cookies.set(SECURITY_COOKIE_NAME, SECURITY_COOKIE_VALUE, path="/")
    except Exception as e:
        logger.warning(
            "Failed to set security cookie, continuing",
            extra={"error": str(e)},
        )


def fetch_login_page(
    session: requests.Session, login_url: str, timeout: int
) -> Optional[requests.Response]:
    """Запрашивает страницу входа и возвращает ответ при успехе, иначе None."""
    try:
        response = session.get(login_url, timeout=timeout)
        if response.status_code != 200:
            logger.warning(
                "Failed to fetch login page",
                extra={"url": login_url, "status_code": response.status_code},
            )
            return None
        return response
    except requests.RequestException as e:
        logger.warning(
            "Request exception while fetching login page",
            extra={"url": login_url, "error": str(e)},
        )
        return None


def is_login_form(form: Form) -> bool:
    """Проверяет, является ли форма формой входа (содержит поля username или user_token)."""
    return any(inp.name in LOGIN_FORM_FIELDS for inp in form.inputs if inp.name)


def extract_login_form(html_text: str, page_url: str) -> Optional[Form]:
    """Извлекает форму входа из HTML-кода страницы."""
    forms = extract_forms(html_text, page_url)
    if not forms:
        logger.warning("No forms found on login page", extra={"url": page_url})
        return None

    login_form = next((f for f in forms if is_login_form(f)), None)
    if login_form:
        return login_form
    return None


def build_login_payload(form: Form, username: str, password: str) -> dict:
    """Формирует словарь данных для POST-запроса входа."""
    payload = {inp.name: inp.value for inp in form.inputs if inp.name}
    payload.update({"username": username, "password": password})
    payload.setdefault(LOGIN_BUTTON_NAME, LOGIN_BUTTON_VALUE)
    return payload


def submit_login_form(
    session: requests.Session, action_url: str, data: dict, timeout: int
) -> None:
    """Отправляет POST-запрос с данными формы входа."""
    try:
        session.post(
            action_url,
            data=data,
            headers=DEFAULT_HEADER,
            timeout=timeout,
            allow_redirects=False,
        )
    except requests.RequestException as e:
        logger.warning(
            "Request exception during login form submission",
            extra={"url": action_url, "error": str(e)},
        )


def verify_login_success(
    session: requests.Session, target_url: str, timeout: int
) -> bool:
    """Проверяет, успешно ли выполнен вход, запрашивая целевой URL."""
    try:
        response = session.get(target_url, timeout=timeout)
    except requests.RequestException as e:
        logger.warning(
            "Request exception during login verification",
            extra={"url": target_url, "error": str(e)},
        )
        return False

    response_text_lower = (response.text or "").lower()

    for indicator in VERIFICATION_FAILURE_INDICATORS:
        if indicator in response.url or indicator in response_text_lower:
            logger.debug(
                "Login verification failed, indicator found",
                extra={"indicator": indicator, "url": response.url},
            )
            return False

    logger.info("Login successful", extra={"target_url": target_url})
    return True
