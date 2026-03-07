from app.core.security import verify_password, hash_password
from app.core.config import settings

# TEMP: replace with DB later
FAKE_USERS = {
    "admin@fincorp.com": {
        "password": hash_password(settings.DEFAULT_LOGIN_PASSWORD),  # Now hashed
        "role": "admin"
    },
    "user@fincorp.com": {
        "password": hash_password(settings.DEFAULT_LOGIN_PASSWORD),  # Now hashed
        "role": "user"
    }
}


def authenticate_user(username: str, password: str):
    user = FAKE_USERS.get(username)
    if not user:
        return None

    # if password != user["password"]:
    #     return None
    if not verify_password(password, user["password"]):
        return None

    return {
        "username": username,
        "role": user["role"]
    }


def register_user(username: str, password: str, role: str = "user"):
    if username in FAKE_USERS:
        return None

    FAKE_USERS[username] = {
        "password": hash_password(password),
        "role": role,
    }

    return {
        "username": username,
        "role": role,
    }


def get_user(username: str):
    user = FAKE_USERS.get(username)
    if not user:
        return None

    return {
        "username": username,
        "role": user["role"],
    }
