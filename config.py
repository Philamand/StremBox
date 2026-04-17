import os

QBT_HOST = os.getenv("QBT_HOST", "localhost")
QBT_PORT = int(os.getenv("QBT_PORT", "8080"))
QBT_USERNAME = os.getenv("QBT_USERNAME", "admin")
QBT_PASSWORD = os.getenv("QBT_PASSWORD", "password")

BASE_DIR = os.getenv("BASE_DIR", "./data/")
