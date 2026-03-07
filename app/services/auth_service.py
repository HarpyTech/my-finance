from pymongo.errors import PyMongoError
import logging

from app.core.security import verify_password, hash_password
from app.core.config import settings
from app.db.mongo import get_users_collection

logger = logging.getLogger(__name__)


def _ensure_default_users() -> None:
    """Ensure default users exist in the database"""
    try:
        logger.debug("Checking for default users")
        users = get_users_collection()
        defaults = [
            {"username": "admin@fincorp.com", "role": "admin"},
            {"username": "user@fincorp.com", "role": "user"},
        ]

        for user in defaults:
            exists = users.find_one({"username": user["username"]}, {"_id": 1})
            if not exists:
                users.insert_one(
                    {
                        "username": user["username"],
                        "password_hash": hash_password(settings.DEFAULT_LOGIN_PASSWORD),
                        "role": user["role"],
                    }
                )
                logger.info(f"Created default user: {user['username']}")
            else:
                logger.debug(f"Default user already exists: {user['username']}")
    except PyMongoError as exc:
        logger.error(
            f"Database error while ensuring default users: {str(exc)}",
            exc_info=True,
        )
        raise


def authenticate_user(username: str, password: str):
    """Authenticate a user with username and password"""
    logger.info(f"Authentication attempt for user: {username}")
    try:
        _ensure_default_users()
        users = get_users_collection()
        user = users.find_one({"username": username})
        if not user:
            logger.warning(f"Authentication failed: User not found - {username}")
            return None

        if not verify_password(password, user["password_hash"]):
            logger.warning(
                f"Authentication failed: Invalid password for user - {username}"
            )
            return None

        logger.info(f"User authenticated successfully: {username}")
        return {
            "username": user["username"],
            "role": user.get("role", "user"),
        }
    except PyMongoError as exc:
        logger.error(
            f"Database error during authentication for user {username}: {str(exc)}",
            exc_info=True,
        )
        raise RuntimeError("Failed to authenticate user due to database error") from exc
    except Exception as exc:
        logger.error(
            f"Unexpected error during authentication for user {username}: {str(exc)}",
            exc_info=True,
        )
        raise


def register_user(username: str, password: str, role: str = "user"):
    """Register a new user"""
    logger.info(f"User registration attempt: {username}")
    try:
        users = get_users_collection()
        exists = users.find_one({"username": username}, {"_id": 1})
        if exists:
            logger.warning(f"Registration failed: User already exists - {username}")
            return None

        users.insert_one(
            {
                "username": username,
                "password_hash": hash_password(password),
                "role": role,
            }
        )

        logger.info(f"User registered successfully: {username} with role: {role}")
        return {
            "username": username,
            "role": role,
        }
    except PyMongoError as exc:
        logger.error(
            f"Database error during registration for user {username}: {str(exc)}",
            exc_info=True,
        )
        raise RuntimeError("Failed to register user due to database error") from exc
    except Exception as exc:
        logger.error(
            f"Unexpected error during registration for user {username}: {str(exc)}",
            exc_info=True,
        )
        raise


def get_user(username: str):
    """Get user information by username"""
    logger.debug(f"Fetching user: {username}")
    try:
        users = get_users_collection()
        user = users.find_one({"username": username})
        if not user:
            logger.warning(f"User not found: {username}")
            return None

        logger.debug(f"User found: {username}")
        return {
            "username": user["username"],
            "role": user.get("role", "user"),
        }
    except PyMongoError as exc:
        logger.error(
            f"Database error while fetching user {username}: {str(exc)}",
            exc_info=True,
        )
        raise RuntimeError("Failed to fetch user due to database error") from exc
    except Exception as exc:
        logger.error(
            f"Unexpected error while fetching user {username}: {str(exc)}",
            exc_info=True,
        )
        raise
