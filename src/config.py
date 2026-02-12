"""
Предоставляет конфигурационные параметры для приложения.
"""
import os

# HTTP / scanner
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "8"))
RATE_LIMIT = float(os.getenv("RATE_LIMIT", "0.5"))

# data
PAYLOADS_PATH = os.getenv("PAYLOADS_PATH", "data/payloads.json")
DEFAULT_DB_PATH = os.getenv("DEFAULT_DB_PATH", "data/data.db")

# logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # DEBUG/INFO/WARNING/ERROR
LOG_FILE = os.getenv("LOG_FILE", "")  # пусто = stdout only

# rules
DEFAULT_RULES = {
    "weights": {"CRITICAL": 10, "HIGH": 6, "MEDIUM": 3, "LOW": 1, "INFO": 0},
    "bonuses": {
        "sql_error": 2,
        "time_delay": 1.5,
        "multiple_payloads": 1,
        "distinct_match_types": 0.5,
    },
    "time_delay_threshold_ms": 200,
}
