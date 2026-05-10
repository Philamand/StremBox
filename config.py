import os

BASE_DIR = os.getenv("BASE_DIR", "./downloads/")
BASE_URL = os.getenv("BASE_URL", "http://localhost").rstrip("/")

BEARER_TOKEN = os.getenv("BEARER_TOKEN", "test_token")

HANKO_URL = os.getenv("HANKO_URL", "http://localhost:8000")
HANKO_ADMIN = os.getenv("HANKO_ADMIN", "")

SQLITE_FILE = os.getenv("SQLITE_FILE", "database.db")

TRANSMISSION_URL = os.getenv("TRANSMISSION_URL", "gluetun")
