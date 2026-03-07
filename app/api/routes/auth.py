from fastapi import APIRouter, HTTPException, Request, Response, status
import logging

from app.core.security import create_access_token
from app.services.auth_service import authenticate_user, register_user
from app.models.user import UserCreate, UserLogin

router = APIRouter()
logger = logging.getLogger(__name__)


COOKIE_NAME = "access_token"


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24,
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def api_register(payload: UserCreate):
    """Register a new user"""
    logger.info("Registration request received")
    try:
        user = register_user(payload.username, payload.password)
    except RuntimeError as exc:
        logger.error(f"Service unavailable during registration: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    if not user:
        logger.warning("Registration failed: User already exists")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    logger.info("User registered successfully")
    return {
        "message": "User registered successfully",
        "user": user,
    }


@router.post("/login")
async def api_login(request: Request, response: Response):
    """
    API login endpoint
    - Used by UI or API clients
    - Supports form and JSON requests
    - Returns JWT and sets session cookie
    """
    logger.info("Login request received")
    content_type = request.headers.get("content-type", "")
    username = ""
    password = ""

    if "application/json" in content_type:
        body = await request.json()
        payload = UserLogin(**body)
        username = payload.username
        password = payload.password
        logger.debug("JSON login attempt received")
    else:
        form = await request.form()
        username = form.get("username", "")
        password = form.get("password", "")
        logger.debug("Form login attempt received")

    if not username or not password:
        logger.warning("Login failed: Missing username or password")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="username and password are required",
        )

    try:
        user = authenticate_user(username, password)
    except RuntimeError as exc:
        logger.error(f"Service unavailable during login: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    if not user:
        logger.warning("Login failed: Invalid credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token({"username": user["username"], "role": user["role"]})

    _set_session_cookie(response, token)

    logger.info(f"User logged in successfully: {username}")
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
    }


@router.post("/logout")
def api_logout(request: Request, response: Response):
    """Log out the current user"""
    user = getattr(request.state, "user", "unknown")
    logger.info(f"User logged out: {user}")
    response.delete_cookie(key=COOKIE_NAME)
    return {"message": "Logged out"}


@router.get("/session")
def api_session(request: Request):
    """Get current session information"""
    user = getattr(request.state, "user", None)
    role = getattr(request.state, "role", None)
    if not user:
        logger.debug("Session check failed: Not authenticated")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    logger.debug(f"Session check successful for user: {user}")
    return {
        "authenticated": True,
        "user": user,
        "role": role,
    }


@router.get("/csrf")
def get_csrf_token(request: Request):
    """Get CSRF token for the current session"""
    token = request.cookies.get("csrf_token")
    logger.debug("CSRF token requested")
    return {"csrf_token": token}
