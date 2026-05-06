import os

TRANSMISSION_HOST = os.getenv("TRANSMISSION_HOST", "localhost")
TRANSMISSION_PORT = int(os.getenv("TRANSMISSION_PORT", "9091"))
TRANSMISSION_USERNAME = os.getenv("TRANSMISSION_USERNAME")
TRANSMISSION_PASSWORD = os.getenv("TRANSMISSION_PASSWORD")

BASE_DIR = os.getenv("BASE_DIR", "./downloads/")

BEARER_TOKEN = os.getenv("BEARER_TOKEN", "test_token")

HANKO_URL = os.getenv("HANKO_URL", "http://localhost:8000")
HANKO_ADMIN = os.getenv("HANKO_ADMIN", "")
