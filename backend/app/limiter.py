
from ipaddress import ip_address

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings


def client_ip(request: Request) -> str:
    """
    Resolve client IP address.

    Forwarded headers are trusted only when the application
    is deployed behind a trusted reverse proxy.
    """

    if settings.TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("x-forwarded-for")

        if forwarded:
            candidate = forwarded.split(",")[0].strip()

            try:
                return str(ip_address(candidate))
            except ValueError:
                pass

    remote_address = get_remote_address(request)

    try:
        return str(ip_address(remote_address))
    except ValueError:
        return "unknown"


limiter = Limiter(
    key_func=client_ip,
    default_limits=[],
    storage_uri="memory://",
    headers_enabled=False,
    enabled=settings.RATE_LIMIT_ENABLED,
)


# Endpoint-specific rate limits
LOGIN_LIMIT = "10/minute"
REGISTER_LIMIT = "5/minute"
OTP_REQUEST_LIMIT = "5/minute"
OTP_RESET_LIMIT = "10/minute"
NOTIFICATION_LIMIT = "5/minute"
PROFILE_LIMIT = "20/minute"
ADMIN_LIMIT = "60/minute"


def rate_limit_handler(
    request: Request,
    exc: RateLimitExceeded,
) -> JSONResponse:
    """
    Return a consistent rate-limit response.
    """

    return JSONResponse(
        status_code=429,
        content={
            "detail": (
                "Terlalu banyak percobaan. "
                "Silakan tunggu sekitar 1 menit lalu coba lagi."
            ),
            "limit": str(exc.detail),
        },
        headers={
            "Retry-After": "60",
            "Cache-Control": "no-store",
        },
    )
