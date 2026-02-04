"""
Модуль предоставляет классы для html объектов и связанные с ними функции

Классы:
    Form (форма htmk)
    InputField (поле формы)

Функции:
    parse_form_inputs (преобразует поля форм, в обьекты InputField)

"""

from dataclasses import dataclass, asdict, field
from typing import Optional, Any, List
from src.extractor.utils import safe_urljoin
from bs4.element import Tag
from src.logger import get_logger

logger = get_logger(__name__)


@dataclass
class InputField:
    """
    Класс представляет из себя абстракцию поля формы html

    Атрибуты:
        name - имя поля
        field_type - тип поля
        value - значение
        required - обязательность поля
        placeholder - размещенный пример ввода
        meta - мета-информация

    Методы:
        from_textarea_tag() - конструктор для textarea поля
        from_select_tag() - конструктор для select поля
        from_input_tag() - конструктор для input поля
        to_dict() - маршализует данные в словарь
    """

    name: Optional[str]
    field_type: Optional[str]
    # textarea -> str, select -> list, input -> str
    value: Optional[Any]
    required: bool
    placeholder: Optional[str]
    # обеспечиваем необязательность meta
    meta: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_textarea_tag(cls, tag: Tag) -> "InputField":
        return cls(
            name=tag.get("name"),
            field_type="textarea",
            value=tag.text or None,
            required=tag.has_attr("required"),
            placeholder=tag.get("placeholder"),
        )

    @classmethod
    def from_input_tag(cls, tag: Tag) -> "InputField":
        return cls(
            name=tag.get("name"),
            field_type=tag.get("type", "text"),
            value=tag.get("value"),
            required=tag.has_attr("required"),
            placeholder=tag.get("placeholder"),
        )

    @classmethod
    def from_select_tag(cls, tag: Tag) -> "InputField":
        options = [
            {
                "value": opt.get("value"),
                "text": opt.text,
                "selected": opt.has_attr("selected"),
            }
            for opt in tag.find_all("option")
        ]
        return cls(
            name=tag.get("name"),
            field_type="select",
            value=options,
            required=tag.has_attr("required"),
            placeholder=tag.get("placeholder"),
            meta={"multiple": tag.has_attr("multiple")},
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Form:
    """
    Класс представляет из себя абстракцию формы html

    Атрибуты:
        action - относительный путь
        method - метод запроса
        inputs - поля
        enctype - кодировка
        form_id - id формы
        classes - класс формы

    Методы:
        to_dict() - маршализует форму в словарь
        from_soup_form() - конструктор из обекта form, bs4
    """

    action: Optional[str]
    method: str
    inputs: List[InputField]
    enctype: Optional[str]
    form_id: Optional[str]
    classes: List[str]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["inputs"] = [inp.to_dict() for inp in self.inputs]
        return d

    @classmethod
    def from_soup_form(cls, form_tag: Tag, base_url: Optional[str] = None) -> Form:
        action = form_tag.get("action", "")
        # Логирование форм без action
        if not action:
            form_id = form_tag.get("id")
            classes = form_tag.get("class", [])
            logger.warning(
                "form without action", extra={"form_id": form_id, "classes": classes}
            )
        action = safe_urljoin(base_url, action)
        return cls(
            action=action,
            method=form_tag.get("method", "get").lower(),
            inputs=parse_form_inputs(form_tag),
            enctype=form_tag.get("enctype"),
            form_id=form_tag.get("id"),
            classes=form_tag.get("class", []),
        )


IGNORED_INPUT_TYPES = {"submit", "button", "reset", "image"}


def parse_form_inputs(form_tag: Tag) -> List[InputField]:
    result: List[InputField] = []
    # Список всех конструкторов поля (для разных типов)
    parsers = {
        "input": InputField.from_input_tag,
        "textarea": InputField.from_textarea_tag,
        "select": InputField.from_select_tag,
    }

    for tag in form_tag.find_all(["input", "textarea", "select"]):

        # Проверка поддержки данного типа поля
        if (
            tag.name == "input"
            and (tag.get("type") or "text").lower() in IGNORED_INPUT_TYPES
        ):
            continue
        parser = parsers.get(tag.name)
        if not parser:
            continue

        try:
            result.append(parser(tag))
        except Exception as e:
            print(f"Failed to parse <{tag.name}>: {e}")
    return result
