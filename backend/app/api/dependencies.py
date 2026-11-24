
from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.auth import verify_csrf_token
from app.config import settings
from app.cookies import (
    ACCESS_COOKIE_NAME,
    REFRESH_COOKIE_NAME,
)


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
    Proteksi CSRF berbasis token bertanda tangan (HMAC).

    Header ``X-CSRF-Token`` wajib berisi token yang diterbitkan server
    pada response login/refresh/session. Token juga tersedia sebagai
    cookie agar aplikasi same-origin dapat membacanya lewat JavaScript.

    Pendekatan ini tetap bekerja saat frontend dan backend berada di
    origin berbeda, karena JavaScript tidak perlu membaca cookie API.
    """

    if request.method.upper() in SAFE_METHODS:
        return

    csrf_header = request.headers.get(CSRF_HEADER_NAME)

    if not csrf_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token tidak ditemukan.",
        )

    if not verify_csrf_token(csrf_header):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token tidak valid.",
        )

    _validate_origin(request)


def _resolve_current_user(
    request: Request,
    response: Response,
    db: Session,
) -> User | None:
    """Cari user dari access token, lalu fallback ke refresh token.

    Fallback ini membuat halaman yang di-refresh tetap login meskipun
    access token (30 menit) sudah kedaluwarsa: cookie baru langsung
    diterbitkan pada response yang sama.
    """

    # Import lokal untuk menghindari circular import saat modul dimuat.
    from app.api.endpoints.auth import (
        _set_auth_cookies,
        _user_from_access_token,
        _user_from_refresh_token,
    )

    user = _user_from_access_token(
        db,
        request.cookies.get(ACCESS_COOKIE_NAME),
    )

    if user:
        return user

    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)

    if not refresh_token:
        return None

    user = _user_from_refresh_token(db, refresh_token)

    if not user:
        return None

    _set_auth_cookies(
        response,
        user,
        request,
    )

    return user


def get_current_user(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> User:
    """
    Autentikasi menggunakan HttpOnly cookie.

    Access token diprioritaskan. Bila sudah kedaluwarsa tetapi refresh
    token masih valid, sesi diperpanjang otomatis tanpa memaksa user
    login ulang. Tidak membaca Authorization: Bearer.
    """

    verify_csrf(request)

    user = _resolve_current_user(request, response, db)

    if user:
        return user

    has_access_cookie = bool(
        request.cookies.get(ACCESS_COOKIE_NAME)
    )
    has_refresh_cookie = bool(
        request.cookies.get(REFRESH_COOKIE_NAME)
    )

    if not has_access_cookie and not has_refresh_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi tidak ditemukan. Silakan login kembali.",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesi tidak valid atau telah kedaluwarsa.",
    )
