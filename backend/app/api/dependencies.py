
import secrets

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.crud import user as crud_user
from app.auth import (
    decode_access_token,
    password_fingerprint,
    verify_csrf_token,
)
from app.config import settings


ACCESS_COOKIE_NAME = "access_token"
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _validate_origin(request: Request) -> None:
    origin = request.headers.get("origin")

    if not origin:
        if settings.APP_ENV == "production":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Origin header wajib disertakan.",
            )

        return

    normalized_origin = origin.strip().rstrip("/").lower()

    allowed_origins = {
        item.strip().rstrip("/").lower()
        for item in settings.cors_origins_list
    }

    if (
        allowed_origins
        and normalized_origin not in allowed_origins
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Origin tidak diizinkan.",
        )


def verify_csrf(request: Request) -> None:
    """
    Signed double-submit cookie CSRF protection.
    Diterapkan pada request yang mengubah data.
    """

    if request.method.upper() in SAFE_METHODS:
        return

    csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
    csrf_header = request.headers.get(CSRF_HEADER_NAME)

    if not csrf_cookie or not csrf_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token tidak ditemukan.",
        )

    if not secrets.compare_digest(
        csrf_cookie,
        csrf_header,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token tidak cocok.",
        )

    if not verify_csrf_token(csrf_cookie):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token tidak valid.",
        )

    _validate_origin(request)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    Autentikasi menggunakan access_token dari HttpOnly cookie.
    Tidak membaca Authorization: Bearer.
    """

    verify_csrf(request)

    access_token = request.cookies.get(ACCESS_COOKIE_NAME)

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi tidak ditemukan. Silakan login kembali.",
        )

    payload = decode_access_token(access_token)

    if not payload or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi tidak valid atau telah kedaluwarsa.",
        )

    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid.",
        )

    user = crud_user.get_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi tidak valid.",
        )

    token_fingerprint = str(payload.get("pwd", ""))
    current_fingerprint = password_fingerprint(
        user.password_hash
    )

    if not secrets.compare_digest(
        token_fingerprint,
        current_fingerprint,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi telah kedaluwarsa. Silakan login kembali.",
        )

    return user
