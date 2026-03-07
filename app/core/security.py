from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
import logging

from app.core.config import settings
import secrets

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_csrf_token():
    """Generate a CSRF token"""
    token = secrets.token_urlsafe(32)
    logger.debug("CSRF token created")
    return token


def create_access_token(data: dict):
    """Create a JWT access token"""
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode.update({"exp": expire})
        token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        logger.debug(
            f"Access token created for user: {data.get('username', 'unknown')}"
        )
        return token
    except Exception as exc:
        logger.error(f"Failed to create access token: {str(exc)}", exc_info=True)
        raise


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    try:
        hashed = pwd_context.hash(password)
        logger.debug("Password hashed successfully")
        return hashed
    except Exception as exc:
        logger.error(f"Failed to hash password: {str(exc)}", exc_info=True)
        raise


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash"""
    try:
        result = pwd_context.verify(password, hashed)
        logger.debug(f"Password verification: {'successful' if result else 'failed'}")
        return result
    except Exception as exc:
        logger.error(f"Error during password verification: {str(exc)}", exc_info=True)
        return False


# def create_access_token(subject: str):
#     expire = datetime.utcnow() + timedelta(
#         minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
#     )
#     payload = {"sub": subject, "exp": expire}
#     return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
