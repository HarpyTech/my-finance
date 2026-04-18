from fastapi import APIRouter, HTTPException, Request, Response, status
import logging

from app.core.security import create_access_token
from app.core.ratelimit import OtpRateLimitError
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
    except OtpRateLimitError as exc:
        logger.warning(f"Rate limit exceeded for registration: {payload.username}")
        response = Response(status_code=429)
        response.headers["Retry-After"] = str(exc.retry_after_seconds)
        return response
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


@router.get("/test-email")
def test_email_delivery(to_email: str):
    """Test SMTP email delivery (development only).

    Public endpoint that sends a test email to the provided address.
    Returns success/failure status and helpful debug info.
    """
    from app.core.config import settings
    import smtplib
    from email.message import EmailMessage

    logger.info(f"Testing email delivery for {to_email}")

    if not settings.SMTP_HOST:
        return {
            "status": "not_configured",
            "message": (
                "SMTP is not configured. Configure SMTP_HOST "
                "in environment to send real emails."
            ),
            "smtp_host": None,
        }

    try:
        subject = "My Finance - Test Email"
        body = (
            "This is a test email from My Finance. "
            "If you received this, SMTP is working correctly!"
        )

        logger.info("Preparing test email message")

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = to_email
        message.set_content(body)

        with smtplib.SMTP(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            timeout=15,
        ) as server:
            server.ehlo()
            if settings.SMTP_USE_TLS:
                if not server.has_extn("STARTTLS"):
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=(
                            "SMTP server does not support STARTTLS. "
                            "Disable SMTP_USE_TLS or use a TLS-capable server."
                        ),
                    )
                server.starttls()
                server.ehlo()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message)

        logger.info(f"Test email sent successfully to {to_email}")
        return {
            "status": "success",
            "message": f"Test email sent to {to_email}",
            "smtp_host": settings.SMTP_HOST,
            "smtp_port": settings.SMTP_PORT,
            "from_email": settings.SMTP_FROM_EMAIL,
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to send test email: {str(exc)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to send test email: {str(exc)}",
        ) from exc
