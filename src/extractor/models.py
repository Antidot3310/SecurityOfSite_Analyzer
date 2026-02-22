"""
Модуль предоставляет классы для представления HTML-форм и полей,
а также функции для парсинга.

Классы:
    Form - представляет HTML-форму
    InputField - представляет поле формы (input, textarea)

Функции:
    parse_form_inputs - преобразует теги полей формы в объекты InputField

"""

from dataclasses import dataclass, asdict
from urllib.parse import urljoin
from typing import Optional, Any, List
from bs4.element import Tag
from src.logger import get_logger

logger = get_logger(__name__)

IGNORED_INPUT_TYPES = {"submit", "button", "reset", "image"}


@dataclass
class InputField:
    """
    Представляет поле HTML-формы.

    Атрибуты:
        name: имя поля
        field_type: тип поля (input type, 'textarea')
        value: значение поля
        required: флаг обязательности
        placeholder: подсказка для input/textarea
        meta: дополнительные данные
    """

    name: Optional[str]
    field_type: Optional[str]
    value: Optional[str]
    required: bool
    placeholder: Optional[str]
    meta: dict[str, Any] = None

    def __post_init__(self):
        if self.meta is None:
            self.meta = {}

    @classmethod
    def from_textarea_tag(cls, tag: Tag) -> "InputField":
        """Создаёт InputField из тега <textarea>."""
        return cls(
            name=tag.get("name"),
            field_type="textarea",
            value=tag.text or None,
            required=tag.has_attr("required"),
            placeholder=tag.get("placeholder"),
        )

    @classmethod
    def from_input_tag(cls, tag: Tag) -> "InputField":
        """Создаёт InputField из тега <input>."""
        return cls(
            name=tag.get("name"),
            field_type=tag.get("type", "text"),
            value=tag.get("value"),
            required=tag.has_attr("required"),
            placeholder=tag.get("placeholder"),
        )


@dataclass
class Form:
    """
    Представляет HTML-форму.

    Атрибуты:
        action: URL отправки
        method: HTTP-метод
        inputs: список полей формы
        enctype: тип кодировки при отправке
        form_id: значение атрибута id (если есть)
    """

    action: str
    method: str
    inputs: List[InputField]
    enctype: Optional[str]
    form_id: Optional[str]

    def to_dict(self) -> dict[str, Any]:
        """Возвращает словарное представление формы."""
        return asdict(self)

    @classmethod
    def from_soup_form(cls, form_tag: Tag, url: str) -> "Form":
        """
        Создаёт объект Form из тега BeautifulSoup.

        Параметры:
            form_tag: тег <form>, полученный из BeautifulSoup
            url: базовый URL страницы

        Возвращает:
            Объект Form.
        """
        action = form_tag.get("action", "")
        if not action:
            form_id = form_tag.get("id")
            logger.warning(
                "Form without action attribute",
                extra={"url": url, "form_id": form_id},
            )
        return cls(
            action=urljoin(url, action),
            method=form_tag.get("method", "get").lower(),
            inputs=parse_form_inputs(form_tag),
            enctype=form_tag.get("enctype"),
            form_id=form_tag.get("id"),
        )


def parse_form_inputs(form_tag: Tag) -> List[InputField]:
    """
    Извлекает все поля ввода из тега формы.

    Параметры:
        form_tag: тег <form>, полученный из BeautifulSoup

    Возвращает:
        Список объектов InputField, соответствующих тегам <input> и <textarea>.
    """
    result: List[InputField] = []
    parsers = {
        "input": InputField.from_input_tag,
        "textarea": InputField.from_textarea_tag,
    }

    for tag in form_tag.find_all(["input", "textarea"]):
        if tag.name == "input":
            tag_type = (tag.get("type") or "text").lower()
            if tag_type in IGNORED_INPUT_TYPES:
                continue
        parser = parsers.get(tag.name)

        try:
            result.append(parser(tag))
        except Exception as e:
            logger.exception(
                "Failed to parse form field",
                extra={
                    "tag_name": tag.name,
                    "tag_html": str(tag)[:200],
                    "error": str(e),
                },
            )
    return result
