"""Rate limiting utilities for signup OTP requests."""

import logging
from datetime import datetime, timedelta, timezone

from app.db.mongo import get_users_collection

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OtpRateLimitError(Exception):
    """Raised when OTP request exceeds rate limit."""

    def __init__(self, message: str, retry_after_seconds: int):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


def check_and_record_otp_request(
    email: str,
    max_attempts: int = 3,
    window_minutes: int = 10,
) -> None:
    """
    Check if email has exceeded OTP request rate limit.
    Raises OtpRateLimitError if limit is exceeded.
    Records the request if allowed.
    """
    try:
        rate_limit_col = get_users_collection().database["signup_otp_attempts"]

        # Create TTL index for auto-cleanup (optional but recommended)
        try:
            rate_limit_col.create_index(
                "created_at",
                expireAfterSeconds=window_minutes * 60,
            )
        except Exception:
            pass

        now = _utcnow()
        window_start = now - timedelta(minutes=window_minutes)

        # Count recent attempts
        recent_count = rate_limit_col.count_documents(
            {
                "email": email,
                "created_at": {"$gte": window_start},
            }
        )

        if recent_count >= max_attempts:
            # Calculate how long user must wait
            oldest_attempt = rate_limit_col.find_one(
                {
                    "email": email,
                    "created_at": {"$gte": window_start},
                },
                sort=[("created_at", 1)],
            )
            if oldest_attempt:
                retry_after = int(
                    (
                        oldest_attempt["created_at"]
                        + timedelta(minutes=window_minutes)
                        - now
                    ).total_seconds()
                )
                retry_after = max(1, retry_after)
            else:
                retry_after = window_minutes * 60

            logger.warning(
                "OTP rate limit exceeded for email %s: " "%d attempts in %d minutes",
                email,
                recent_count,
                window_minutes,
            )
            raise OtpRateLimitError(
                f"Too many OTP requests. Please try again in {retry_after} seconds.",
                retry_after,
            )

        # Record this request
        rate_limit_col.insert_one(
            {
                "email": email,
                "created_at": now,
            }
        )
        logger.debug(
            "OTP request recorded for email %s: %d/%d attempts",
            email,
            recent_count + 1,
            max_attempts,
        )

    except OtpRateLimitError:
        raise
    except Exception as exc:
        logger.error(
            "Error checking OTP rate limit for %s: %s",
            email,
            str(exc),
            exc_info=True,
        )
        raise RuntimeError("Failed to check rate limit") from exc


def clear_otp_attempts(email: str) -> None:
    """Clear all OTP attempts for an email after successful verification."""
    try:
        rate_limit_col = get_users_collection().database["signup_otp_attempts"]
        rate_limit_col.delete_many({"email": email})
        logger.debug("Cleared OTP attempts for email %s", email)
    except Exception as exc:
        logger.warning(
            "Failed to clear OTP attempts for %s: %s",
            email,
            str(exc),
        )
