"""
Предоставляет конфигурационные параметры для приложения.
"""

# HTTP / scanner
REQUEST_TIMEOUT = 8
TIME_DELAY_THRESHOLD_MS = 2000
RATE_LIMIT = 0.0
DEFAULT_HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0 Gecko/20100101 Firefox/147.0"
}

# data
SQL_ERRORS_PATH = "data/sql_errors.json"
PAYLOADS_PATH = "data/payloads.json"
DEFAULT_DB_PATH = "data/data.db"

# logging
LOG_LEVEL = "DEBUG"
