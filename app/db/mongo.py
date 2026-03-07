from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: MongoClient | None = None


def get_mongo_client() -> MongoClient:
    """Get or create MongoDB client connection"""
    global _client
    if _client is None:
        try:
            logger.info(f"Connecting to MongoDB at {settings.MONGODB_URI}")
            _client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=3000)
            # Test the connection
            _client.admin.command("ping")
            logger.info("Successfully connected to MongoDB")
        except PyMongoError as exc:
            logger.error(f"Failed to connect to MongoDB: {str(exc)}", exc_info=True)
            raise
    return _client


def get_database() -> Database:
    """Get the application database"""
    try:
        db = get_mongo_client()[settings.MONGODB_DB]
        logger.debug(f"Accessing database: {settings.MONGODB_DB}")
        return db
    except Exception as exc:
        logger.error(f"Failed to access database: {str(exc)}", exc_info=True)
        raise


def get_users_collection() -> Collection:
    """Get the users collection with indexes"""
    try:
        collection = get_database()["users"]
        # Ensure unique index on username
        collection.create_index("username", unique=True)
        logger.debug("Users collection accessed with indexes ensured")
        return collection
    except PyMongoError as exc:
        logger.error(f"Failed to access users collection: {str(exc)}", exc_info=True)
        raise
    except Exception as exc:
        logger.error(
            f"Unexpected error accessing users collection: {str(exc)}",
            exc_info=True,
        )
        raise


def get_expenses_collection() -> Collection:
    """Get the expenses collection with indexes"""
    try:
        collection = get_database()["expenses"]
        # Ensure indexes for efficient queries
        collection.create_index([("username", 1), ("expense_date", -1)])
        collection.create_index([("username", 1), ("bill_type", 1)])
        logger.debug("Expenses collection accessed with indexes ensured")
        return collection
    except PyMongoError as exc:
        logger.error(f"Failed to access expenses collection: {str(exc)}", exc_info=True)
        raise
    except Exception as exc:
        logger.error(
            f"Unexpected error accessing expenses collection: {str(exc)}",
            exc_info=True,
        )
        raise


def ping_database() -> bool:
    """Ping the database to check connectivity"""
    try:
        get_mongo_client().admin.command("ping")
        logger.debug("Database ping successful")
        return True
    except PyMongoError as exc:
        logger.warning(f"Database ping failed: {str(exc)}")
        return False
    except Exception as exc:
        logger.error(
            f"Unexpected error during database ping: {str(exc)}", exc_info=True
        )
        return False
