import os

BASE_DIR = os.getenv("BASE_DIR", "./downloads/")
BASE_URL = os.getenv("BASE_URL", "http://localhost").rstrip("/")

BEARER_TOKEN = os.getenv("BEARER_TOKEN", "test_token")

HANKO_URL = os.getenv("HANKO_URL", "http://localhost:8000")
HANKO_ADMIN = os.getenv("HANKO_ADMIN", "")

DATABASE_URL = os.getenv("DATABASE_URL_TEST", "database/database.db")

TRANSMISSION_URL = os.getenv("TRANSMISSION_URL", "gluetun")

ORIGIN_URL = os.getenv("ORIGIN_URL", "http://localhost:8000")
