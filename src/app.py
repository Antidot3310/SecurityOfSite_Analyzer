import json
from typing import Any, Optional
from pathlib import Path
from flask import Flask, request, jsonify
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.extractor.extractor import extract_forms, fetch_html
from src.storage.db import init_db, save_scan
from src.scanner.scanner import scan_forms
from src.scanner.payloads import load_payloads

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


@app.route("/dummy", methods=["GET", "POST"])
def dummy():
    vals = request.values.to_dict(flat=False)
    s = ""
    for k, v in vals.items():
        if isinstance(v, list):
            s += " " + v[0]
        else:
            s += " " + str(v)
    if "OR 1=1" in s or "UNION SELECT" in s:
        return f"Database error: you have an error in your sql syntax", 200
    if "SLEEP" in s.upper() or "SLEEP(" in s:
        import time

        time.sleep(2.5)
        return f"Delayed response (simulated)", 200
    return f"<html><body>{s}</body></html>", 200


@app.route("/api/scan", methods=["GET"])
def api_scan():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "missing url"}), 400
    forms_res = parse_forms_from_url(url)
    forms = forms_res["forms"]

    payloads = load_payloads("data/payloads.json")
    findings = scan_forms(forms, payloads, rate_limit=0.2)

    findings_jsonable = [f.to_dict() for f in findings]
    scan_id = save_scan(
        target=url,
        results_json=json.dumps({"forms": forms, "findings": findings_jsonable}),
        meta={
            "count": len(findings),
            "status_code": 200,
            "response_size": forms_res["html_length"],
        },
    )
    return (
        jsonify(
            {
                "scan_id": scan_id,
                "findings_count": len(findings),
                "findings": findings_jsonable,
            }
        ),
        200,
    )


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
