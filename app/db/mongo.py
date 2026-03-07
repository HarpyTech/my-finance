from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.core.config import settings


_client: MongoClient | None = None


def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=3000)
    return _client


def get_database() -> Database:
    return get_mongo_client()[settings.MONGODB_DB]


def get_users_collection() -> Collection:
    collection = get_database()["users"]
    collection.create_index("username", unique=True)
    return collection


def get_expenses_collection() -> Collection:
    collection = get_database()["expenses"]
    collection.create_index([("username", 1), ("expense_date", -1)])
    collection.create_index([("username", 1), ("bill_type", 1)])
    return collection


def ping_database() -> bool:
    try:
        get_mongo_client().admin.command("ping")
        return True
    except PyMongoError:
        return False
