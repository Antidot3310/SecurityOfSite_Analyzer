"""
Модуль предоставляет каркас Flask-приложения для парсинга и сканирования веб-форм.

Эндпоинты:
    /api/parse – парсинг форм с целевого URL.
    /api/scan  – сканирование целевого URL на уязвимости.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import requests
from flask import Flask, request, jsonify

from src.extractor.extractor import extract_forms
from src.extractor.auth import try_login_dvwa
from src.storage.db import init_db, save_scan
from src.scanner.scanner import scan_forms
from src.scanner.types import load_payloads, Payload
from src.ml.aggregator import prepare_and_cluster
from src.config import RATE_LIMIT, PAYLOADS_PATH, DEFAULT_HEADER
from src.logger import get_logger

logger = get_logger(__name__)

app = Flask(__name__)

ERROR_MISSING_URL = "Missing 'url' parameter"
ERROR_SCANNER_NOT_INIT = "Scanner not initialized"
ERROR_FETCH_FAILED = "fetch_failed"

try:
    PAYLOADS: list[Payload] = load_payloads(PAYLOADS_PATH)
except Exception as e:
    logger.exception(
        "Failed to load payloads on startup", extra={"path": PAYLOADS_PATH}
    )
    PAYLOADS = []


def save_scan_results(target: str, results_json: str) -> int:
    """Сохраняет результаты в БД и возвращает scan_id."""
    scan_id = save_scan(target=target, results_json=results_json)
    logger.info("Scan results saved", extra={"target": target, "scan_id": scan_id})
    return scan_id


def prepare_session() -> requests.Session:
    """Создаёт и настраивает сессию."""
    session = requests.Session()
    session.headers.update(DEFAULT_HEADER)
    return session


def attempt_dvwa_login(session: requests.Session, url: str) -> None:
    """Пытается выполнить автоматический вход в DVWA, логирует ошибки."""
    try:
        try_login_dvwa(session, url)
    except Exception:
        logger.exception("DVWA autologin failed", extra={"url": url})


def fetch_page(session: requests.Session, url: str) -> requests.Response:
    """Выполняет GET-запрос к целевому URL."""
    try:
        response = session.get(url, allow_redirects=True)
        response.raise_for_status()  
        return response
    except requests.RequestException as e:
        logger.exception("Failed to fetch target", extra={"url": url, "error": str(e)})
        raise


def extract_forms_from_response(response: requests.Response) -> list[dict]:
    """Извлекает формы из HTML-ответа и возвращает их в виде списка словарей."""
    forms = extract_forms(response.text, response.url)
    return [f.to_dict() for f in forms]


def perform_scan(forms: list[dict], session: requests.Session) -> list[dict]:
    """Запускает сканирование форм с использованием загруженных полезных нагрузок."""
    findings = scan_forms(forms, PAYLOADS, RATE_LIMIT, session)
    return [f.to_dict() for f in findings]


@app.route("/api/scan", methods=["GET"])
def api_scan():
    url = request.args.get("url")
    logger.info("API scan request", extra={"url": url})

    if not url:
        logger.warning("Missing url parameter")
        return jsonify({"error": ERROR_MISSING_URL}), 400

    if not PAYLOADS:
        logger.error("No payloads loaded")
        return jsonify({"error": ERROR_SCANNER_NOT_INIT}), 500

    session = prepare_session()
    attempt_dvwa_login(session, url)

    try:
        response = fetch_page(session, url)
    except requests.RequestException as e:
        return jsonify({"error": ERROR_FETCH_FAILED, "reason": str(e)}), 400

    forms = extract_forms_from_response(response)
    findings = perform_scan(forms, session)
    aggregated_findings = prepare_and_cluster(findings)

    result_data = {
        "findings": findings,
        "findings_count": len(findings),
        "aggregated_findings": aggregated_findings,
    }
    save_scan_results(target=url, results_json=json.dumps(result_data))

    return jsonify(result_data), 200


@app.route("/api/parse", methods=["GET"])
def api_parse():
    url = request.args.get("url")
    logger.info("API parse request", extra={"url": url})

    if not url:
        logger.warning("Missing url parameter")
        return jsonify({"error": ERROR_MISSING_URL}), 400

    session = prepare_session()
    attempt_dvwa_login(session, url)

    try:
        response = fetch_page(session, url)
    except requests.RequestException as e:
        return jsonify({"error": ERROR_FETCH_FAILED, "reason": str(e)}), 400

    forms = extract_forms_from_response(response)

    result_data = {
        "forms": forms,
        "forms_count": len(forms),
    }
    save_scan_results(target=url, results_json=json.dumps(forms))

    return jsonify(result_data), 200


if __name__ == "__main__":
    try:
        init_db("data/data.db")
    except Exception as e:
        logger.exception("Failed to initialize database")
    app.run()
