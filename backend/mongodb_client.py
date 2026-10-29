"""MongoDB Atlas connection client and helper functions for CanteenIQ backend."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Locate backend_db/.env or local .env
ENV_PATHS = [
    Path(__file__).resolve().parents[1] / "backend_db" / ".env",
    Path(__file__).resolve().parent / ".env",
]

for p in ENV_PATHS:
    if p.exists():
        load_dotenv(p)
        break

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://shahanaacs24_db_user:shanu0212@han-clust0.wtj2ost.mongodb.net/"
)
DATABASE_NAME = os.getenv("MONGODB_DATABASE", "menumind")

_client: Optional[MongoClient] = None
_db = None


def get_mongo_client() -> MongoClient:
    """Return a singleton MongoClient instance."""
    global _client
    if _client is None:
        _client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=120000,
            timeoutMS=120000,
        )
    return _client


def get_mongo_db():
    """Return the active MongoDB database object."""
    global _db
    if _db is None:
        client = get_mongo_client()
        _db = client[DATABASE_NAME]
    return _db


def check_mongo_connection() -> Dict[str, Any]:
    """Verify live connectivity to MongoDB Atlas and return collection document counts."""
    try:
        client = get_mongo_client()
        client.admin.command("ping")
        db = get_mongo_db()
        cols = db.list_collection_names()
        counts = {}
        for c in cols:
            counts[c] = db[c].count_documents({})

        return {
            "connected": True,
            "database": DATABASE_NAME,
            "collections_count": len(cols),
            "collection_stats": counts,
            "status": "ONLINE",
            "message": "Successfully connected to MongoDB Atlas cluster",
        }
    except (ConnectionFailure, ServerSelectionTimeoutError) as err:
        return {
            "connected": False,
            "database": DATABASE_NAME,
            "collections_count": 0,
            "collection_stats": {},
            "status": "OFFLINE",
            "message": f"MongoDB Atlas connection unavailable: {str(err)}",
        }
    except Exception as e:
        return {
            "connected": False,
            "database": DATABASE_NAME,
            "collections_count": 0,
            "collection_stats": {},
            "status": "ERROR",
            "message": f"Unexpected error connecting to MongoDB Atlas: {str(e)}",
        }
