"""Rate limiting terpusat memakai slowapi.

Tujuan: mencegah brute-force kata sandi/OTP dan spam request dari satu IP
tanpa perlu membatasi CORS (IP laptop pameran bisa berubah-ubah).

Catatan penting:
- Penyimpanan memakai memori proses (`memory://`). Cukup untuk satu proses
  uvicorn seperti saat pameran. Kalau nanti dijalankan multi-worker, ganti
  ke Redis lewat env `RATE_LIMIT_STORAGE_URI`.
- `RATE_LIMIT_ENABLED=false` bisa dipakai saat load-test lokal.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
    headers_enabled=False,
    enabled=settings.RATE_LIMIT_ENABLED,
)

LOGIN_LIMIT = "10/minute"
REGISTER_LIMIT = "5/minute"
OTP_REQUEST_LIMIT = "5/minute"
OTP_RESET_LIMIT = "10/minute"
NOTIFICATION_LIMIT = "5/minute"
PROFILE_LIMIT = "20/minute"
ADMIN_LIMIT = "60/minute"


def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Kembalikan pesan Indonesia dengan field `detail` agar frontend konsisten."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Terlalu banyak percobaan. Silakan tunggu sekitar 1 menit lalu coba lagi.",
            "limit": str(exc.detail),
        },
        headers={"Retry-After": "60"},
    )
