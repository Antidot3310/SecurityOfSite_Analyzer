from dataclasses import dataclass, asdict, field
from src.utils import safe_urljoin
from typing import Optional, Any, List


@dataclass
class InputField:
    name: Optional[str]
    field_type: Optional[str]
    value: Optional[str]  # init value
    required: bool
    placeholder: Optional[str]  # text when no value is set
    meta: dict[str, Any] = field(default_factory=dict)  # movable field

    @classmethod
    def from_textarea_tag(cls, tag) -> InputField:
        return cls(
            name=tag.get("name"),
            field_type="textarea",
            value=tag.text or None,
            required=tag.has_attr("required"),
            placeholder=tag.get("placeholder"),
        )

    @classmethod
    def from_input_tag(cls, tag) -> InputField:
        return cls(
            name=tag.get("name"),
            field_type=tag.get("type", "text"),
            value=tag.get("value"),
            required=tag.has_attr("required"),
            placeholder=tag.get("placeholder"),
        )

    @classmethod
    def from_select_tag(cls, tag) -> InputField:
        options = []
        for option in tag.find_all("option"):
            options.append(
                {
                    "value": option.get("value"),
                    "text": option.text,
                    "selected": option.has_attr("selected"),
                }
            )

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
    inputs: list[InputField]
    enctype: Optional[str]
    form_id: str
    classes: list[str]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["inputs"] = [input_field.to_dict() for input_field in self.inputs]
        return result

    @classmethod
    def from_soup_form(cls, form_tag, base_url: Optional[str] = None) -> Form:
        action = form_tag.get("action")
        if action and base_url:
            action = safe_urljoin(base_url, action)

        return cls(
            action=action or base_url,
            method=form_tag.get("method", "get").lower(),
            enctype=form_tag.get("enctype"),
            form_id=form_tag.get("id"),
            classes=form_tag.get("class", []),
            inputs=parse_form_inputs(form_tag),
        )


# save inputs with different structure (tags) correctly
def parse_form_inputs(form_tag) -> List[InputField]:
    inputs = []

    tag_parsers = {
        "input": InputField.from_input_tag,
        "textarea": InputField.from_textarea_tag,
        "select": InputField.from_select_tag,
    }

    for tag in form_tag.find_all(["input", "textarea", "select"]):
        if tag.name == "input" and tag.get("type") in [
            "submit",
            "button",
            "reset",
            "image",
        ]:
            continue
        parser = tag_parsers.get(tag.name)
        if parser:
            try:
                inputs.append(parser(tag))
            except Exception as e:
                print(f"Failed to parse {tag.name} tag: {e}")

    return inputs
