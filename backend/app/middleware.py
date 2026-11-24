
from starlette.requests import Request
from starlette.responses import Response


DOCS_PATHS = (
    "/docs",
    "/redoc",
    "/openapi.json",
)

DOCS_CSP = (
    "default-src 'self'; "
    "img-src 'self' data: https://fastapi.tiangolo.com; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net "
    "https://fonts.googleapis.com; "
    "font-src 'self' data: https://fonts.gstatic.com; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'none'; "
    "form-action 'none'"
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
    "Permissions-Policy": (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=()"
    ),
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "cross-origin",
    "X-Permitted-Cross-Domain-Policies": "none",
}


class SecurityHeadersMiddleware:

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)

        path = request.url.path

        is_docs = (
            path in DOCS_PATHS
            or path.startswith("/docs/")
            or path.startswith("/redoc/")
        )

        is_https = request.url.scheme == "https"

        if not is_https:
            from app.config import settings

            if settings.TRUST_PROXY_HEADERS:
                forwarded_proto = request.headers.get(
                    "x-forwarded-proto",
                    "",
                )

                is_https = (
                    forwarded_proto.split(",")[0].strip().lower()
                    == "https"
                )

        async def send_with_security_headers(message):

            if message["type"] == "http.response.start":

                headers = list(message.get("headers", []))

                existing_headers = {
                    key.lower()
                    for key, _ in headers
                }

                security_headers = dict(BASE_HEADERS)

                security_headers["Content-Security-Policy"] = (
                    DOCS_CSP if is_docs else API_CSP
                )

                if is_https:
                    security_headers["Strict-Transport-Security"] = (
                        "max-age=31536000; includeSubDomains"
                    )

                for name, value in security_headers.items():

                    if name.lower().encode() not in existing_headers:
                        headers.append(
                            (
                                name.lower().encode(),
                                value.encode("latin-1"),
                            )
                        )

                message["headers"] = headers

            await send(message)

        await self.app(
            scope,
            receive,
            send_with_security_headers,
        )
