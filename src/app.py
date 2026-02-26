"""
Модуль предоставляет каркас Flask-приложения для парсинга и сканирования веб-форм.

Эндпоинты:
    /api/parse – парсинг форм с целевого URL.
    /api/scan  – сканирование целевого URL на уязвимости.
    /dummy     – тестовый эндпоинт.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
from typing import Any, Dict
from flask import Flask, request, jsonify

from src.extractor.extractor import extract_forms, fetch_html
from src.storage.db import init_db, save_scan
from src.scanner.scanner import scan_forms
from src.scanner.types import load_payloads, Payload
from src.config import RATE_LIMIT, PAYLOADS_PATH
from src.logger import get_logger

logger = get_logger(__name__)

app = Flask(__name__)

try:
    PAYLOADS: list[Payload] = load_payloads(PAYLOADS_PATH)
except Exception as e:
    logger.exception(
        "Failed to load payloads on startup", extra={"path": PAYLOADS_PATH}
    )
    PAYLOADS = []


def save_scan_results(target: str, results_json: str, meta: dict) -> int:
    """Сохраняет результаты в БД и возвращает scan_id."""
    scan_id = save_scan(target=target, results_json=results_json, meta=meta)
    logger.info("Scan results saved", extra={"target": target, "scan_id": scan_id})
    return scan_id


def parse_forms_from_url(url: str) -> Dict[str, Any]:
    """
    Получает HTML по URL и извлекает формы.

    Возвращает словарь с ключами:
        forms (list) – список форм в виде словарей,
        html_length (int) – длина HTML,
        forms_count (int) – количество форм.

    Исключения:
        ConnectionError – если не удалось получить HTML.
    """
    html = fetch_html(url)
    if html is None:
        raise ConnectionError(f"Could not fetch HTML from {url}")

    forms = extract_forms(html, url)
    return {
        "forms": [form.to_dict() for form in forms],
        "html_length": len(html),
        "forms_count": len(forms),
    }


@app.route("/dummy", methods=["GET", "POST"])
def dummy():
    # получаем все агументы body как словарь
    vals = request.values.to_dict(flat=False)
    s = ""
    # конкатенируем все аргументы в строку, чтобы не проверять каждый по отдельности
    for k, v in vals.items():
        if isinstance(v, list):
            s += " " + v[0]
        else:
            s += " " + str(v)
    if "OR 1=1" in s or "UNION SELECT" in s:
        # SQLI
        return f"Database error: you have an error in your sql syntax", 200
    if "SLEEP" in s.upper() or "SLEEP(" in s:
        import time

        time.sleep(2.5)
        # time-based
        return f"Delayed response (simulated)", 200
    # XSS
    return f"<html><body>{s}</body></html>", 200


@app.route("/api/scan", methods=["GET"])
def api_scan():
    url = request.args.get("url")
    logger.info("API scan request", extra={"url": url})
    if not url:
        logger.warning("Missing url parameter")
        return jsonify({"error": "Missing 'url' parameter"}), 400

    if not PAYLOADS:
        logger.error("No payloads loaded")
        return jsonify({"error": "Scanner not properly initialized"}), 500

    try:
        forms_res = parse_forms_from_url(url)
    except ConnectionError as e:
        logger.error("Failed to fetch HTML", extra={"url": url, "error": str(e)})
        return jsonify({"error": "Could not retrieve the resource"}), 502

    try:
        findings = scan_forms(forms_res["forms"], PAYLOADS, rate_limit=RATE_LIMIT)
    except Exception as e:
        logger.exception("Scanning failed", extra={"url": url})
        return jsonify({"error": "Scanning failed"}), 500

    scan_id = save_scan_results(
        target=url,
        results_json=json.dumps(
            {"forms": forms_res["forms"], "findings": [f.to_dict() for f in findings]}
        ),
        meta={
            "count": len(findings),
            "status_code": 200,
            "response_size": forms_res["html_length"],
        },
    )

    logger.info(
        "Scan finished",
        extra={
            "url": url,
            "scan_id": scan_id,
            "forms_count": len(forms_res["forms"]),
            "findings_count": len(findings),
        },
    )

    # возврат находок в удобном формате
    return (
        jsonify(
            {
                "scan_id": scan_id,
                "findings_count": len(findings),
                "findings": [f.to_dict() for f in findings],
            }
        ),
        200,
    )


@app.route("/api/parse", methods=["GET"])
def api_parse():
    url = request.args.get("url")
    logger.info("API parse request", extra={"url": url})
    if not url:
        logger.warning("missing url parameter")
        return jsonify({"error": "missing url parameter"}), 400

    try:
        res = parse_forms_from_url(url)
    except ConnectionError as e:
        logger.error("Failed to fetch HTML", extra={"url": url, "error": str(e)})
        return jsonify({"error": "Could not retrieve the resource"}), 502

    scan_id = save_scan_results(
        target=url,
        results_json=json.dumps(res),
        meta={
            "count": res["forms_count"],
            "status_code": 200,
            "response_size": res["html_length"],
        },
    )

    return (
        jsonify(
            {
                "scan_id": scan_id,
                "forms_count": res["forms_count"],
                "forms": res["forms"],
            }
        ),
        200,
    )


if __name__ == "__main__":
    try:
        init_db("data/data.db")
    except Exception as e:
        logger.exception("Failed to initialize database")
    app.run()
