"""Middleware keamanan: header HTTP pelindung browser.

Lapisan ini tidak berhubungan dengan IP/CORS, jadi aman dipakai saat pameran
di LAN yang alamat IP-nya berubah-ubah.

Header yang dipasang:
- ``X-Content-Type-Options: nosniff`` -> browser tidak menebak-nebak tipe file.
- ``X-Frame-Options: DENY`` + ``frame-ancestors 'none'`` -> anti clickjacking.
- ``Referrer-Policy: no-referrer`` -> alamat halaman tidak bocor ke situs lain.
- ``Permissions-Policy`` -> matikan kamera/mikrofon/lokasi yang tidak dipakai.
- ``Cross-Origin-Opener-Policy`` -> isolasi window dari situs lain.
- ``Content-Security-Policy`` -> API hanya boleh memuat dirinya sendiri;
  halaman dokumentasi (/docs, /redoc) diberi pengecualian karena Swagger UI
  memuat aset dari CDN dan menjalankan skrip inline.
- ``Strict-Transport-Security`` -> HANYA dikirim jika request sudah HTTPS,
  supaya tidak memaksa browser ke HTTPS saat demo LAN masih memakai http.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Halaman dokumentasi interaktif butuh CDN + skrip inline.
DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")

DOCS_CSP = (
    "default-src 'self'; "
    "img-src 'self' data: https://fastapi.tiangolo.com; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
    "font-src 'self' data: https://fonts.gstatic.com; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'none'"
)

API_CSP = (
    "default-src 'none'; "
    "frame-ancestors 'none'; "
    "base-uri 'none'; "
    "form-action 'none'"
)

BASE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    # `cross-origin` agar frontend di port/IP berbeda tetap boleh mengambil data.
    "Cross-Origin-Resource-Policy": "cross-origin",
    "X-Permitted-Cross-Domain-Policies": "none",
}


def _is_https(request: Request) -> bool:
    forwarded = request.headers.get("x-forwarded-proto", "")
    if forwarded:
        return forwarded.split(",")[0].strip().lower() == "https"
    return request.url.scheme == "https"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        for header, value in BASE_HEADERS.items():
            response.headers.setdefault(header, value)

        path = request.url.path
        is_docs = path in DOCS_PATHS or path.startswith("/docs/")
        response.headers.setdefault(
            "Content-Security-Policy", DOCS_CSP if is_docs else API_CSP
        )

        if _is_https(request):
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )

        return response
