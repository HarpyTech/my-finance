from fastapi import APIRouter, HTTPException, Request, Response, status
import logging

from app.core.security import create_access_token
from app.services.auth_service import (
    authenticate_user,
    register_user,
    verify_user_signup_otp,
)
from app.models.user import UserCreate, UserLogin, UserVerifySignup

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
    """Start registration by generating OTP and sending it to email"""
    logger.info("Registration OTP request received")
    try:
        user = register_user(payload.username, payload.password)
    except RuntimeError as exc:
        logger.error(f"Service unavailable during registration: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    if not user:
        logger.warning("Registration failed: User already exists and verified")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    logger.info("Registration OTP sent successfully")
    return {
        "message": "OTP sent to your email. Verify to complete registration.",
        "user": user,
    }


@router.post("/register/verify", status_code=status.HTTP_200_OK)
def api_verify_register(payload: UserVerifySignup):
    """Verify OTP and activate user account"""
    logger.info("Registration OTP verification request received")
    try:
        result = verify_user_signup_otp(payload.username, payload.otp)
    except RuntimeError as exc:
        logger.error(f"Service unavailable during OTP verification: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if result.get("error") == "OTP expired":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired. Please register again to receive a new OTP.",
        )

    if result.get("error") == "Invalid OTP":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP",
        )

    return {
        "message": "Email verified successfully. You can now log in.",
        "user": result,
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

    if user.get("requires_verification"):
        logger.warning("Login failed: User email not verified")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email using OTP.",
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
