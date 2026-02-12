"""
Модуль предоставляет каркас flask приложения с несколькими эндпоинтами

Эндпоинты:
    /api/parse - сканирует html целевого ресурса и парсит все формы
    /api/scan - сканирует целевой ресурс на уязвимости
    /dummy - симулирует sql ошибки, явные xss и временные задержки  (для теста)

Функции:
    save_to_file() - вспомогательная функция сохранения ответа /api/parse в файл
    parse_forms_from_url() - выносит логику получения форм из html кода целевого ресурса
"""

# добавление корня проекта в переменную PATH для корректной работы
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
from typing import Any, Optional
from pathlib import Path
from flask import Flask, request, jsonify

from src.extractor.extractor import extract_forms, fetch_html
from src.storage.db import init_db, save_scan
from src.scanner.scanner import scan_forms
from src.scanner.types import load_payloads
from src.agregator.io import export_findings, sample_findings
from src.config import RATE_LIMIT, PAYLOADS_PATH
from src.logger import get_logger
from src.agregator.rulebased import aggregate_findings

logger = get_logger(__name__)


app = Flask(__name__)


def save_to_file(data: list[dict[str, Any]], filename: str) -> None:
    """
    Записывает список Form в json файл
    """
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
    """
    Сканирует целевой ресурс на уязвимости
    """
    # получение url из body запроса
    url = request.args.get("url")
    # логирование начала запроса
    logger.info(
        "API scan request", extra={"url": url, "client_ip": request.remote_addr}
    )
    if not url:
        logger.warning("missing url parameter")
        return jsonify({"error": "missing url"}), 400

    forms_res = parse_forms_from_url(url)
    forms = forms_res["forms"]

    # получение уязвимостей путем отправки пэйлойдов и их анализа
    payloads = load_payloads(PAYLOADS_PATH)
    logger.info(
        "Loaded payloads", extra={"count": len(payloads), "path": PAYLOADS_PATH}
    )
    findings = scan_forms(forms, payloads, rate_limit=RATE_LIMIT)

    # сохранение в бд
    scan_id = save_scan(
        target=url,
        results_json=json.dumps(
            {"forms": forms, "findings": [f.to_dict() for f in findings]}
        ),
        meta={
            "count": len(findings),
            "status_code": 200,
            "response_size": forms_res["html_length"],
        },
    )
    # логирование результата сканирования
    if scan_id is None:
        logger.exception(
            "Scan not saved", extra={"url": url, "forms": forms, "findings": findings}
        )
    logger.info(
        "Scan finished",
        extra={
            "url": url,
            "scan_id": scan_id,
            "forms_count": len(forms),
            "findings_count": len(findings),
        },
    )
    normalized_findings = export_findings(findings, scan_id=scan_id)
    aggregated_findings = aggregate_findings(normalized_findings)
    # возврат находок в удобном формате
    return (
        jsonify(
            {
                "scan_id": scan_id,
                "findings_count": len(findings),
                "aggregated_findings": aggregated_findings,
            }
        ),
        200,
    )


@app.route("/api/parse", methods=["GET"])
def api_parse():
    """
    Эндпоинт парсит html код целевого ресурса
    и возвращает список форм в удобном формате,
    также сохраняет его в бд и отдельный файл.
    """
    # получение url из body запроса
    url: Optional[str] = request.args.get("url")
    # логирование начала запроса
    logger.info(
        "API parse request", extra={"url": url, "client_ip": request.remote_addr}
    )
    if not url:
        logger.warning("missing url parameter")
        return jsonify({"error": "missing url parameter"}), 400

    try:
        # получаем формы и сохраняем в бд
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

        # сохраняем еще в файл для удобного перепросмотра
        filename = "tests/test_data/Result.json"
        save_to_file(res["forms"], filename)
        logger.info("Saved result file", extra={"path": filename})

        # даем ответ в приложение
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
        logger.exception(
            "api_parse error", exc_info=True, extra={"url": url, "error": str(e)}
        )
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    try:
        init_db("data/data.db")
    except Exception as e:
        logger.exception("Failed to initialize database", exc_info=True)
    app.run(debug=True)
