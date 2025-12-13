from dataclasses import dataclass, asdict, field
from typing import Optional, Any, List
from src.extractor.utils import safe_urljoin
from bs4.element import Tag


@dataclass
class InputField:
    name: Optional[str]
    field_type: Optional[str]
    value: Optional[Any]  # textarea -> str, select -> list, input -> str
    required: bool
    placeholder: Optional[str]
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
        action = form_tag.get("action")
        if base_url and action:
            action = safe_urljoin(base_url, action)
        action = action or base_url
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
    parsers = {
        "input": InputField.from_input_tag,
        "textarea": InputField.from_textarea_tag,
        "select": InputField.from_select_tag,
    }

    for tag in form_tag.find_all(["input", "textarea", "select"]):
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
