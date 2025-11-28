import os
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root not in sys.path:
    sys.path.insert(0, root)

from flask import Flask, request, jsonify
from src.extractor import *
import json


app = Flask("__name__")


@app.route("/api/parse", methods=["GET"])
def api_parse():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "missing url parametr"}), 400
    else:
        try:
            html = fetch_html(url)
            if html is None:
                return jsonify({"error": "failed to fetch html"})
            forms = extract_forms(html)
            res = [form.to_dict() for form in forms]
            with open("Result.json", "w", encoding="UTF-8") as file:
                json.dump(res, file, ensure_ascii=True, indent=2)
            return jsonify({"count": len(res), "forms": res})
        except Exception as e:
            return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
