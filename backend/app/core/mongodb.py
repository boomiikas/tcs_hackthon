import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

# Load backend/.env
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_PATH)

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("MONGODB_DATABASE", "menumind")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI is missing")

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=10000
)

db = client[DATABASE_NAME]


def check_connection():
    client.admin.command("ping")
    return True


def get_database():
    return db