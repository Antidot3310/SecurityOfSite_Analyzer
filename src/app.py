from flask import Flask, request, jsonify
from src.extractor import extract_forms, fetch_html
from src.storage.db import init_db, save_scan
from typing import Any
import json
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


app = Flask(__name__)


def save_to_file(data: list[dict[str, Any]], filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


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


# return forms from site
# takes url as parameter
# support as relative as absolute pathes
@app.route("/api/parse", methods=["GET"])
def api_parse():
    url = request.args.get("url")
    if not url:
        return (
            jsonify({"error": "missing url parameter"}),
            400,
        )  # return tuple

    try:
        res = parse_forms_from_url(url)  # if problem raise exception
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
        return jsonify(
            {"count": res["forms_count"], "scan_id": scan_id, "forms": res["forms"]}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
