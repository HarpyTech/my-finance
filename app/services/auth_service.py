from pymongo.errors import PyMongoError

from app.core.security import verify_password, hash_password
from app.core.config import settings
from app.db.mongo import get_users_collection


def _ensure_default_users() -> None:
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


def authenticate_user(username: str, password: str):
    try:
        _ensure_default_users()
        users = get_users_collection()
        user = users.find_one({"username": username})
        if not user:
            return None

        if not verify_password(password, user["password_hash"]):
            return None

        return {
            "username": user["username"],
            "role": user.get("role", "user"),
        }
    except PyMongoError as exc:
        raise RuntimeError("Failed to authenticate user due to database error") from exc


def register_user(username: str, password: str, role: str = "user"):
    try:
        users = get_users_collection()
        exists = users.find_one({"username": username}, {"_id": 1})
        if exists:
            return None

        users.insert_one(
            {
                "username": username,
                "password_hash": hash_password(password),
                "role": role,
            }
        )

        return {
            "username": username,
            "role": role,
        }
    except PyMongoError as exc:
        raise RuntimeError("Failed to register user due to database error") from exc


def get_user(username: str):
    try:
        users = get_users_collection()
        user = users.find_one({"username": username})
        if not user:
            return None

        return {
            "username": user["username"],
            "role": user.get("role", "user"),
        }
    except PyMongoError as exc:
        raise RuntimeError("Failed to fetch user due to database error") from exc
