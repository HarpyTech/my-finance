from pymongo.errors import PyMongoError
import logging
import random
from datetime import datetime, timedelta, timezone
import socket
import smtplib
from email.message import EmailMessage

from app.core.security import verify_password, hash_password
from app.core.config import settings
from app.core.ratelimit import (
    check_and_record_otp_request,
    clear_otp_attempts,
    OtpRateLimitError,
)
from app.db.mongo import get_users_collection

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_otp_expired(expires_at: datetime | None) -> bool:
    if not expires_at:
        return True
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return _utcnow() > expires_at


def _generate_signup_otp() -> str:
    digits = max(4, min(settings.SIGNUP_OTP_LENGTH, 8))
    return "".join(random.choices("0123456789", k=digits))


def _build_signup_otp_email_html(recipient: str, otp: str) -> str:
    expiry_minutes = settings.SIGNUP_OTP_EXPIRY_MINUTES
    return f"""<!doctype html>
<html>
<head>
    <meta charset=\"utf-8\" />
    <title>Verify your FinTrackr account</title>
</head>
<body style=\"margin:0;padding:20px;background:#f6f8fb;\">
    <table width=\"100%\" role=\"presentation\" cellspacing=\"0\" cellpadding=\"0\">
        <tr>
            <td align=\"center\">
                <table width=\"620\" role=\"presentation\" cellspacing=\"0\" cellpadding=\"0\"
                             style=\"max-width:620px;background:#fff;border:1px solid #e5e7eb;\">
                    <tr>
                        <td style=\"padding:14px 18px;background:#0f172a;color:#fff;\">
                            <table width=\"100%\" role=\"presentation\" cellspacing=\"0\" cellpadding=\"0\">
                                <tr>
                                    <td align=\"left\" style=\"font-weight:700;font-size:14px;\">Branch LOGO</td>
                                    <td align=\"right\" style=\"font-weight:700;font-size:14px;\">
                                        FinTrackr Name Logo
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td style=\"padding:22px 20px;font:15px/1.5 Arial,Helvetica,sans-serif;\">
                            <p style=\"margin:0 0 12px 0;\">Hello {recipient},</p>
                            <p style=\"margin:0 0 12px 0;\">
                                You received this email because a verification request was made for your
                                FinTrackr account.
                            </p>
                            <p style=\"margin:0 0 8px 0;\"><strong>Your OTP is:</strong></p>
                            <p style=\"margin:0 0 12px 0;font-size:30px;letter-spacing:4px;color:#1d4ed8;\">
                                <strong>{otp}</strong>
                            </p>
                            <p style=\"margin:0 0 12px 0;\">This OTP expires in {expiry_minutes} minutes.</p>
                            <p style=\"margin:0 0 16px 0;\">
                                If you did not initiate this request, please ignore this email.
                            </p>
                            <p style=\"margin:0 0 6px 0;\">Thanks &amp; Regards,</p>
                            <p style=\"margin:0;font-weight:700;\">Support Team</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def _deliver_signup_otp(email: str, otp: str) -> None:
    subject = "Verify your FinTrackr account"
    body = (
        "Your FinTrackr verification code is: "
        f"{otp}. "
        "This code expires in "
        f"{settings.SIGNUP_OTP_EXPIRY_MINUTES} minutes."
    )

    if not settings.SMTP_HOST:
        logger.warning(
            "SMTP is not configured. OTP for %s is %s (development fallback).",
            email,
            otp,
        )
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = email
    if settings.SMTP_BCC_EMAILS:
        message["Bcc"] = ", ".join(settings.SMTP_BCC_EMAILS)
    message.set_content(body)
    message.add_alternative(
        _build_signup_otp_email_html(email, otp),
        subtype="html",
    )

    try:
        smtp_client = smtplib.SMTP_SSL if settings.SMTP_USE_SSL else smtplib.SMTP

        with smtp_client(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            timeout=settings.SMTP_TIMEOUT_SECONDS,
        ) as server:
            if not settings.SMTP_USE_SSL:
                server.ehlo()
                if settings.SMTP_USE_TLS:
                    if not server.has_extn("STARTTLS"):
                        raise RuntimeError(
                            "SMTP server does not support STARTTLS. "
                            "Disable SMTP_USE_TLS or use a TLS-capable server."
                        )
                    server.starttls()
                    server.ehlo()

            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

            server.send_message(message)

        logger.info("Verification OTP email sent to %s", email)
    except (
        TimeoutError,
        socket.timeout,
        smtplib.SMTPServerDisconnected,
    ) as exc:
        logger.error(
            ("Failed to send OTP email to %s " "due to SMTP timeout/disconnect: %s"),
            email,
            str(exc),
            exc_info=True,
        )
        mode = "ssl" if settings.SMTP_USE_SSL else "plain/starttls"
        raise RuntimeError(
            "SMTP connection timed out or was closed by server. "
            f"host={settings.SMTP_HOST} "
            f"port={settings.SMTP_PORT} "
            f"mode={mode}."
        ) from exc
    except Exception as exc:
        logger.error(
            "Failed to send OTP email to %s: %s",
            email,
            str(exc),
            exc_info=True,
        )
        raise RuntimeError("Failed to send verification email") from exc


def authenticate_user(username: str, password: str):
    """Authenticate a user with username and password"""
    logger.info("Authentication attempt initiated")
    try:
        users = get_users_collection()
        user = users.find_one({"username": username})
        if not user:
            logger.warning("Authentication failed: User not found")
            return None

        if not verify_password(password, user["password_hash"]):
            logger.warning("Authentication failed: Invalid password")
            return None

        if not user.get("email_verified", False):
            logger.warning("Authentication failed: Email not verified")
            return {"requires_verification": True}

        # Record the login timestamp to enable per-session rate limiting.
        users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login_at": _utcnow()}},
        )

        logger.info("User authenticated successfully")
        return {
            "username": user["username"],
            "role": user.get("role", "user"),
        }
    except PyMongoError as exc:
        logger.error(
            f"Database error during authentication: {str(exc)}",
            exc_info=True,
        )
        raise RuntimeError("Failed to authenticate user due to database error") from exc
    except Exception as exc:
        logger.error(
            f"Unexpected error during authentication: {str(exc)}",
            exc_info=True,
        )
        raise


def register_user(username: str, password: str, role: str = "user"):
    """Create or refresh an unverified user and send signup OTP."""
    logger.info("User registration OTP request initiated")
    try:
        check_and_record_otp_request(username)
        users = get_users_collection()
        existing_user = users.find_one({"username": username})
        if existing_user and existing_user.get("email_verified", False):
            logger.warning("Registration failed: User already exists and is verified")
            return None

        otp = _generate_signup_otp()
        otp_expires_at = _utcnow() + timedelta(
            minutes=settings.SIGNUP_OTP_EXPIRY_MINUTES
        )
        update_doc = {
            "username": username,
            "password_hash": hash_password(password),
            "role": role,
            "email_verified": False,
            "expense_limit": 10,
            "disable_rate_limit": False,
            "signup_otp_hash": hash_password(otp),
            "signup_otp_expires_at": otp_expires_at,
            "updated_at": _utcnow(),
        }

        if existing_user:
            users.update_one(
                {"_id": existing_user["_id"]},
                {"$set": update_doc},
            )
        else:
            users.insert_one({**update_doc, "created_at": _utcnow()})

        _deliver_signup_otp(username, otp)

        logger.info(f"OTP generated for user registration with role: {role}")
        return {
            "username": username,
            "role": role,
            "verification_required": True,
        }
    except OtpRateLimitError:
        logger.warning(f"OTP rate limit exceeded for {username}")
        raise
    except PyMongoError as exc:
        logger.error(
            f"Database error during registration: {str(exc)}",
            exc_info=True,
        )
        raise RuntimeError("Failed to register user due to database error") from exc
    except Exception as exc:
        logger.error(
            f"Unexpected error during registration: {str(exc)}",
            exc_info=True,
        )
        raise


def resend_signup_otp(username: str):
    """Resend OTP for users who registered but are still unverified."""
    logger.info("Signup OTP resend request initiated")
    try:
        check_and_record_otp_request(username)
        users = get_users_collection()
        user = users.find_one({"username": username})
        if not user:
            logger.warning("OTP resend failed: User not found")
            return None

        if user.get("email_verified", False):
            logger.warning("OTP resend failed: User already verified")
            return {"error": "already_verified"}

        otp = _generate_signup_otp()
        otp_expires_at = _utcnow() + timedelta(
            minutes=settings.SIGNUP_OTP_EXPIRY_MINUTES
        )

        users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "signup_otp_hash": hash_password(otp),
                    "signup_otp_expires_at": otp_expires_at,
                    "updated_at": _utcnow(),
                }
            },
        )

        _deliver_signup_otp(username, otp)
        logger.info("OTP resend successful")
        return {
            "username": username,
            "verification_required": True,
        }
    except OtpRateLimitError:
        logger.warning(f"OTP resend rate limit exceeded for {username}")
        raise
    except PyMongoError as exc:
        logger.error(
            f"Database error during OTP resend: {str(exc)}",
            exc_info=True,
        )
        raise RuntimeError("Failed to resend OTP due to database error") from exc
    except Exception as exc:
        logger.error(
            f"Unexpected error during OTP resend: {str(exc)}",
            exc_info=True,
        )
        raise


def verify_user_signup_otp(username: str, otp: str):
    """Verify user OTP and activate account for login"""
    logger.info("Signup OTP verification attempt initiated")
    try:
        users = get_users_collection()
        user = users.find_one({"username": username})
        if not user:
            logger.warning("Signup OTP verification failed: User not found")
            return None

        if user.get("email_verified", False):
            logger.info("Signup OTP verification skipped: User already verified")
            return {
                "username": user["username"],
                "role": user.get("role", "user"),
                "already_verified": True,
            }

        otp_hash = user.get("signup_otp_hash")
        otp_expires_at = user.get("signup_otp_expires_at")
        if not otp_hash or _is_otp_expired(otp_expires_at):
            logger.warning("Signup OTP verification failed: OTP expired or missing")
            return {"error": "OTP expired"}

        if not verify_password(otp, otp_hash):
            logger.warning("Signup OTP verification failed: Invalid OTP")
            return {"error": "Invalid OTP"}

        users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "email_verified": True,
                    "updated_at": _utcnow(),
                },
                "$unset": {
                    "signup_otp_hash": "",
                    "signup_otp_expires_at": "",
                },
            },
        )

        clear_otp_attempts(username)
        logger.info("User email verified successfully")
        return {
            "username": user["username"],
            "role": user.get("role", "user"),
            "email_verified": True,
        }
    except PyMongoError as exc:
        logger.error(
            f"Database error during signup OTP verification: {str(exc)}",
            exc_info=True,
        )
        raise RuntimeError("Failed to verify user due to database error") from exc
    except Exception as exc:
        logger.error(
            f"Unexpected error during signup OTP verification: {str(exc)}",
            exc_info=True,
        )
        raise


def get_user(username: str):
    """Get user information by username"""
    logger.debug("Fetching user information")
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


def get_user_profile(username: str):
    """Get user profile with editable PII fields"""
    logger.debug("Fetching user profile")
    try:
        users = get_users_collection()
        user = users.find_one({"username": username})
        if not user:
            logger.warning(f"User profile not found: {username}")
            return None

        logger.debug(f"User profile found: {username}")
        return {
            "username": user["username"],
            "role": user.get("role", "user"),
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "phone": user.get("phone"),
            "address": user.get("address"),
            "expense_limit": user.get("expense_limit", 10),
            "disable_rate_limit": user.get("disable_rate_limit", False),
        }
    except PyMongoError as exc:
        logger.error(
            f"Database error while fetching profile {username}: {str(exc)}",
            exc_info=True,
        )
        raise RuntimeError(
            "Failed to fetch user profile due to database error"
        ) from exc
    except Exception as exc:
        logger.error(
            f"Unexpected error while fetching profile {username}: {str(exc)}",
            exc_info=True,
        )
        raise


def update_user_profile(
    username: str,
    first_name: str | None = None,
    last_name: str | None = None,
    phone: str | None = None,
    address: str | None = None,
):
    """Update editable user PII profile fields"""
    logger.info(f"Updating user profile: {username}")

    def _clean(value: str | None):
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed if trimmed else None

    try:
        users = get_users_collection()
        update_doc = {
            "first_name": _clean(first_name),
            "last_name": _clean(last_name),
            "phone": _clean(phone),
            "address": _clean(address),
        }

        result = users.update_one({"username": username}, {"$set": update_doc})
        if result.matched_count == 0:
            logger.warning(f"User not found for profile update: {username}")
            return None

        return get_user_profile(username)
    except PyMongoError as exc:
        logger.error(
            f"Database error while updating profile {username}: {str(exc)}",
            exc_info=True,
        )
        raise RuntimeError(
            "Failed to update user profile due to database error"
        ) from exc
    except Exception as exc:
        logger.error(
            f"Unexpected error while updating profile {username}: {str(exc)}",
            exc_info=True,
        )
        raise
