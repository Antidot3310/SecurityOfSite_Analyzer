from .scanner import ResponseSnapshot, Payload
from typing import List

# Если нужен простой список без уровней уверенности
SQL_ERROR_LIST = [
    # Самые частые и явные ошибки
    "you have an error in your sql syntax",
    "sql syntax error",
    "unclosed quotation mark",
    "incorrect syntax near",
    "syntax error at or near",
    # MySQL ошибки
    "mysql_fetch_array",
    "mysql_fetch_assoc",
    "mysql_fetch_row",
    "mysql_num_rows",
    "mysql_result",
    "mysql_query",
    "mysqli_",
    "mysql_",
    "warning: mysql",
    "error 1064",
    "error 1146",
    "error 1054",
    # PostgreSQL
    "postgresql",
    "postgres",
    "pg_",
    "relation does not exist",
    "column does not exist",
    # MSSQL
    "microsoft sql server",
    "sql server",
    "mssql",
    "incorrect syntax",
    "invalid column",
    "invalid object",
    "msg 102",
    "msg 207",
    "msg 208",
    "odbc",
    # Oracle
    "ora-",
    "oracle",
    "pl/sql",
    "plsql",
    "ora-00933",
    "ora-00904",
    "ora-00942",
    # SQLite
    "sqlite",
    "sqlite3",
    "no such table",
    "no such column",
    # Общие
    "sql error",
    "database error",
    "query failed",
    "unknown column",
    "table doesn't exist",
]


class DetectedResult:
    def __init__(self, matched: bool, evidence: str):
        self.matched = matched
        self.evidence = evidence

    def to_dict(self):
        return {
            "matched": self.matched,
            "evidence": self.evidence,
        }


def detect_reflection(
    base: ResponseSnapshot, injected: ResponseSnapshot, payload: Payload
) -> dict:
    if (
        payload.payload.lower() in injected.body.lower()
        and payload.payload.lower() not in base.body.lower()
    ):
        return {"matched": True, "evidence": f"Payload reflected: {payload.payload}"}
    return {"matched": False, "evidence": ""}


def detect_sql_error(
    base: ResponseSnapshot, injected: ResponseSnapshot, payload: Payload
) -> dict:
    for err in SQL_ERROR_LIST:
        if err in injected.body.lower() and not err in base.body.lower():
            return DetectedResult(
                matched=True, evidence=payload.evidence_patterns
            ).to_dict()
    return {"matched": False, "evidence": ""}


def detect_time_delay(
    base: ResponseSnapshot, injected: ResponseSnapshot, payload: Payload
) -> dict:
    threshold_ms = 2000  # ms
    if injected.response_time - base.response_time > threshold_ms:
        return {
            "matched": True,
            "evidence": f"Time delay detected: {injected.response_time - base.response_time} ms",
        }
    return {"matched": False, "evidence": ""}


def run_detectors(
    base: ResponseSnapshot, injected: ResponseSnapshot, payload: Payload
) -> List[dict]:
    detectors = [detect_sql_error, detect_reflection, detect_time_delay]
    det_res = []
    for detector in detectors:
        dr = detector(base, injected, payload)
        if dr and dr["matched"]:
            det_res.append(dr)
    return det_res
