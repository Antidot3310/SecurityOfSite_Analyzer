import sys
import json
from typing import List, Optional
from bs4 import BeautifulSoup
import requests


class InputField:
    def __init__(
        self,
        name: Optional[str],
        field_type: Optional[str],
        value: Optional[str],
        required: bool,
        placeholder: Optional[str],
        meta: Optional[dict],
    ):
        self.name = name
        self.field_type = field_type
        self.value = value
        self.required = required
        self.placeholder = placeholder
        self.meta = meta

    def to_dict(self):
        return {
            "name": self.name,
            "field_type": self.field_type,
            "value": self.value,
            "required": self.required,
            "placeholder": self.placeholder,
            "meta": self.meta,
        }


class Form:
    def __init__(
        self,
        action: Optional[str],
        method: str,
        inputs: list[InputField],
        enctype: Optional[str],
        form_id: str,
        classes: str,
    ):
        self.action = action
        self.method = method
        self.enctype = enctype
        self.form_id = form_id
        self.classes = classes
        self.inputs = inputs

    def to_dict(self):
        return {
            "action": self.action,
            "method": self.method,
            "enctype": self.enctype,
            "form_id": self.form_id,
            "classes": self.classes,
            "inputs": [input.to_dict() for input in self.inputs],
        }


def parse_input_tag(input_tag) -> InputField:
    name = input_tag.get("name") or None
    field_type = input_tag.get("type") or "text"
    value = input_tag.get("value") or None
    required = input_tag.has_attr("required")
    placeholder = input_tag.get("placeholder") or None
    meta = {}
    return InputField(name, field_type, value, required, placeholder, meta)


def parse_textarea_tag(textarea_tag) -> InputField:
    name = textarea_tag.get("name")
    field_type = "textarea"
    value = textarea_tag.text or None
    required = textarea_tag.has_attr("required")
    placeholder = textarea_tag.get("placeholder") or None
    meta = {}
    return InputField(name, field_type, value, required, placeholder, meta)


def parse_select_tag(select_tag) -> InputField:
    name = select_tag.get("name")
    field_type = "select"
    value = None
    required = select_tag.has_attr("required")
    placeholder = select_tag.get("placeholder") or None
    multiple = select_tag.has_attr("multiple")
    meta = {"multiple": multiple} if multiple else {}
    options = []
    for option in select_tag.find_all("option"):
        value = option.get("value")
        text = option.text
        selected = option.has_attr("selected")
        options.append({"value": value, "text": text, "selected": selected})
    value = options
    return InputField(name, field_type, value, required, placeholder, meta)


def extract_forms(html: str) -> List[Form]:
    soup = BeautifulSoup(html, "lxml")
    forms = []
    for form in soup.find_all("form"):
        action = form.get("action")
        method = form.get("method", "get")
        form_id = form.get("id") or None
        classes = form.get("class")
        if not classes:
            classes = []
        enctype = form.get("enctype")
        inputs = []
        for tag in form.find_all(["input", "textarea", "select"]):
            if tag.name == "input":
                input_field = parse_input_tag(tag)
            elif tag.name == "textarea":
                input_field = parse_textarea_tag(tag)
            elif tag.name == "select":
                input_field = parse_select_tag(tag)
            inputs.append(input_field)
        forms.append(Form(action, method, inputs, enctype, form_id, classes))
    return forms


def fetch_html(url: str, timeout: int = 4):
    if url.startswith("file://"):
        with open(url[7:], "r", encoding="utf-8") as file:
            content = file.read()
            return content
    else:
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "scanner-mvp/0.1"},
            verify=False,
        )
        try:
            response.raise_for_status()
            return response.text
        except requests.HTTPError as e:
            print(f"HTTP error occured: {e}")
            return None


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "file://D:/Project/src/local.html"
    html = fetch_html(url)
    forms = extract_forms(html)
    print(f"Parsed site: {url}")
    print(json.dumps([form.to_dict() for form in forms], indent=2))
    with open("forms.json", "w", encoding="utf-8") as file:
        json.dump([form.to_dict() for form in forms], file, indent=2)


if __name__ == "__main__":
    main()
