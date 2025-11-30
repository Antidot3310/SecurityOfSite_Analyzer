import sys
import json
from typing import List, Optional
from bs4 import BeautifulSoup
import requests


class InputField:
    def __init__(self, name: Optional[str], type: Optional[str], value: Optional[str]):
        self.name = name
        self.type = type
        self.value = value

    def to_dict(self):
        return {"name": self.name, "type": self.type, "value": self.value}


class Form:
    def __init__(self, action: Optional[str], method: str, inputs: list[InputField]):
        self.action = action
        self.method = method
        self.inputs = inputs

    def to_dict(self):
        return {
            "action": self.action,
            "method": self.method,
            "inputs": [input.to_dict() for input in self.inputs],
        }


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


def extract_forms(html: str) -> List[Form]:
    soup = BeautifulSoup(html, "lxml")
    forms = []
    for form in soup.find_all("form"):
        action = form.get("action")
        method = form.get("method", "get")
        inputs = []
        for input in form.find_all("input"):
            name = input.get("name")
            type = input.get("type")
            value = input.get("value")
            inputs.append(InputField(name, type, value))
        forms.append(Form(action, method, inputs))
    return forms


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
