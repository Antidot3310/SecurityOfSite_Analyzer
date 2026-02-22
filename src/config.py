"""
Предоставляет конфигурационные параметры для приложения.
"""

import os

# HTTP / scanner
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "8"))
RATE_LIMIT = float(os.getenv("RATE_LIMIT", "0.1"))
DEFAULT_USER_AGENT = os.getenv("DEFAULT_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0")

# data
PAYLOADS_PATH = os.getenv("PAYLOADS_PATH", "data/payloads.json")
DEFAULT_DB_PATH = os.getenv("DEFAULT_DB_PATH", "data/data.db")

# logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # DEBUG/INFO/WARNING/ERROR
LOG_FILE = os.getenv("LOG_FILE", "")  # пусто = stdout only

# rules
DEFAULT_RULES = {
    "weights": {"INFO": 0, "LOW": 1, "MEDIUM": 3, "HIGH": 6, "CRITICAL": 9},
    "bonuses": {
        "sql_error": 3,
        "time_delay": 2,
        "multiple_payloads": 1,
        "distinct_match_types": 1,
    },
    "time_delay_threshold_ms": 2000,
    "sql_signatures": [
        "you have an error in your sql syntax",
        "sql syntax error",
        "error 1064",
        "sqlite",
        "postgres",
        "oracle",
        "mysql",
        "sql error",
    ],
    "max_score": 20,
}
