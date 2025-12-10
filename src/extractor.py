from dataclasses import dataclass, asdict, field
from typing import List, Optional, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import requests
from pathlib import Path
from src.parser import url_to_path


@dataclass
class InputField:
    name: Optional[str]
    field_type: Optional[str]
    value: Optional[str]  # init value
    required: bool
    placeholder: Optional[str]  # text when no value is set
    meta: dict[str, Any] = field(default_factory=dict)

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


def safe_urljoin(base: str, url: str) -> str:
    try:
        return urljoin(base, url)
    except Exception as e:
        print(f"Error during operation urljoin: {str(e)}")
        return url


def parse_form_inputs(form_tag) -> List[InputField]:
    inputs = []

    tag_parsers = {
        "input": InputField.from_input_tag,
        "textarea": InputField.from_textarea_tag,
        "select": InputField.from_select_tag,
    }

    for tag in form_tag.find_all(["input", "textarea", "select"]):
        parser = tag_parsers.get(tag.name)
        if parser:
            try:
                inputs.append(parser(tag))
            except Exception as e:
                print(f"Failed to parse {tag.name} tag: {e}")

    return inputs


def extract_forms(html: str, url: Optional[str]) -> List[Form]:
    if not html:
        return []
    try:
        soup = BeautifulSoup(html, "lxml")
        return [Form.from_soup_form(form, url) for form in soup.find_all("form")]
    except Exception as e:
        print(f"Error during extracting forms from html: {str(e)}")
        return []


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
        response = requests.get(url, timeout, headers={"User-Agent": "MVP-Scanner 0.1"})
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error during reading html from web: {str(e)}")


def fetch_html(url: str, timeout: int = 10) -> Optional[str]:
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()

    if scheme == "file":
        path = url_to_path(url)
        return read_html_file(path)

    else:
        return read_html_web(url, timeout)
