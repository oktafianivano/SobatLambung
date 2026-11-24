"""Kebijakan cookie autentikasi.

Modul ini menjadi satu-satunya sumber kebenaran untuk nama cookie dan
atribut keamanannya (Secure, SameSite, Domain, Partitioned). Tujuannya
agar cookie yang dibuat saat login sama persis dengan cookie yang dipakai
saat refresh dan logout, sehingga browser tidak menyimpan dua versi cookie
yang saling bertabrakan.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlparse

from fastapi import Request

from app.config import settings


ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"
CSRF_COOKIE_NAME = "csrf_token"


# Public suffix dua tingkat yang umum dipakai di Indonesia/internasional.
# Dipakai hanya untuk menebak registrable domain saat menentukan same-site.
_MULTI_LABEL_SUFFIXES = {
    "ac.id",
    "co.id",
    "com.br",
    "com.id",
    "com.my",
    "com.sg",
    "co.in",
    "co.jp",
    "co.nz",
    "co.uk",
    "go.id",
    "gov.uk",
    "mil.id",
    "net.au",
    "net.id",
    "org.au",
    "org.id",
    "org.uk",
    "sch.id",
    "web.id",
}


@dataclass(frozen=True)
class CookiePolicy:
    secure: bool
    samesite: str
    domain: Optional[str]
    partitioned: bool


def _registrable_site(host: str) -> str:
    """Perkiraan registrable domain dari sebuah hostname.

    Contoh: ``api.sobatlambung.id`` -> ``sobatlambung.id``.
    Hostname berupa IP atau localhost dikembalikan apa adanya.
    """

    host = (host or "").strip().lower().strip(".")

    if not host:
        return ""

    # IPv6 literal, misalnya "[::1]".
    if host.startswith("[") or ":" in host:
        return host

    parts = host.split(".")

    if len(parts) <= 2:
        return host

    last_two = ".".join(parts[-2:])

    if last_two in _MULTI_LABEL_SUFFIXES:
        return ".".join(parts[-3:])

    return last_two


def is_cross_site_request(request: Request) -> bool:
    """True bila request berasal dari site yang berbeda dari API.

    Penentuan memakai header ``Origin`` yang dikirim browser pada request
    CORS. Bila header tidak ada (mis. health check server-ke-server),
    request dianggap same-site agar tidak memaksa SameSite=None.
    """

    origin = request.headers.get("origin")

    if not origin:
        return False

    try:
        origin_host = urlparse(origin).hostname
    except ValueError:
        return True

    request_host = request.url.hostname

    if not origin_host or not request_host:
        return False

    origin_host = origin_host.lower()
    request_host = request_host.lower()

    if origin_host == request_host:
        return False

    # Bila cookie dibagikan lewat parent domain (mis. .sobatlambung.id),
    # kedua host berada di site yang sama.
    if (
        settings.COOKIE_DOMAIN
        and origin_host.endswith(settings.COOKIE_DOMAIN)
        and request_host.endswith(settings.COOKIE_DOMAIN)
    ):
        return False

    return _registrable_site(origin_host) != _registrable_site(request_host)


def resolve_cookie_policy(request: Optional[Request] = None) -> CookiePolicy:
    """Hitung atribut cookie yang aman untuk request saat ini."""

    secure = settings.cookie_secure
    samesite = settings.COOKIE_SAMESITE

    if samesite == "auto":
        samesite = "none" if request is not None and is_cross_site_request(request) else "lax"

    # Browser menolak SameSite=None tanpa Secure. Ini juga menutup kasus
    # development lintas host yang berjalan di atas HTTP.
    if samesite == "none" and not secure:
        samesite = "lax"

    partitioned = settings.COOKIE_PARTITIONED

    if partitioned is None:
        partitioned = samesite == "none"

    if not secure or samesite != "none":
        partitioned = False

    return CookiePolicy(
        secure=secure,
        samesite=samesite,
        domain=settings.COOKIE_DOMAIN,
        partitioned=partitioned,
    )


def cookie_expiry(max_age_seconds: int) -> datetime:
    """Waktu kedaluwarsa eksplisit untuk cookie persisten.

    ``Max-Age`` saja sudah cukup di browser modern, tetapi ``Expires``
    ikut dikirim agar cookie tetap persisten di WebView/browser lama.
    """

    return datetime.now(timezone.utc) + timedelta(seconds=max_age_seconds)


def access_cookie_max_age() -> int:
    return settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def refresh_cookie_max_age() -> int:
    return settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
