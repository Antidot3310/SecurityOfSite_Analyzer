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
