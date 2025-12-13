import json
from typing import Any, Optional
from pathlib import Path
from flask import Flask, request, jsonify
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.extractor.extractor import extract_forms, fetch_html
from src.storage.db import init_db, save_scan

app = Flask(__name__)


def save_to_file(data: list[dict[str, Any]], filename: str) -> None:
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_forms_from_url(url: str) -> dict[str, Any]:
    html = fetch_html(url)
    if html is None:
        raise ConnectionError("Couldn't get html")

    forms = extract_forms(html, url)
    return {
        "forms": [form.to_dict() for form in forms],
        "html_length": len(html),
        "forms_count": len(forms),
    }


@app.route("/api/parse", methods=["GET"])
def api_parse():
    url: Optional[str] = request.args.get("url")
    if not url:
        return jsonify({"error": "missing url parameter"}), 400

    try:
        res = parse_forms_from_url(url)
        scan_id = save_scan(
            target=url,
            results_json=json.dumps(res),
            meta={
                "count": res["forms_count"],
                "status_code": 200,
                "response_size": res["html_length"],
            },
        )

        save_to_file(res["forms"], "tests/test_data/Result.json")

        return (
            jsonify(
                {
                    "count": res["forms_count"],
                    "scan_id": scan_id,
                    "forms": res["forms"],
                    "response_size": res["html_length"],
                    "status_code": 200,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    init_db("data/data.db")
    app.run(debug=True)
