"""Kebijakan cookie autentikasi.

Modul ini menjadi satu-satunya sumber kebenaran untuk nama cookie dan
atribut keamanannya (Secure, SameSite, Domain, Partitioned). Tujuannya
agar cookie yang dibuat saat login sama persis dengan cookie yang dipakai
saat refresh dan logout, sehingga browser tidak menyimpan dua versi cookie
yang saling bertabrakan.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlparse

from fastapi import Request

from app.config import settings


logger = logging.getLogger("sobat_lambung")

ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"
CSRF_COOKIE_NAME = "csrf_token"


# Public suffix yang umum dipakai. Dipakai untuk menentukan registrable
# domain (eTLD+1) saat memutuskan same-site vs cross-site.
# Sumber: https://publicsuffix.org/list/public_suffix_list.dat
_PUBLIC_SUFFIXES = {
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
    "fly.dev",
    "github.io",
    "go.id",
    "gov.uk",
    "herokuapp.com",
    "mil.id",
    "net.au",
    "net.id",
    "netlify.app",
    "onrender.com",
    "org.au",
    "org.id",
    "org.uk",
    "pages.dev",
    "sch.id",
    "up.railway.app",
    "vercel.app",
    "web.id",
    "workers.dev",
}


@dataclass(frozen=True)
class CookiePolicy:
    secure: bool
    samesite: str
    domain: Optional[str]
    partitioned: bool


def _registrable_site(host: str) -> str:
    """Perkiraan registrable domain (eTLD+1) dari sebuah hostname.

    Contoh:
    - ``api.sobatlambung.id`` -> ``sobatlambung.id``
    - ``foo.up.railway.app`` -> ``foo.up.railway.app`` (public suffix
      ``up.railway.app``, jadi setiap subdomain Railway adalah site berbeda)

    Hostname berupa IP atau localhost dikembalikan apa adanya.
    """

    host = (host or "").strip().lower().strip(".")

    if not host:
        return ""

    # IPv6 literal, misalnya "[::1]".
    if host.startswith("[") or ":" in host:
        return host

    labels = host.split(".")

    # IPv4 literal.
    if len(labels) == 4 and all(
        part.isdigit() for part in labels
    ):
        return host

    if len(labels) <= 2:
        return host

    # Cari public suffix terpanjang yang cocok, lalu ambil satu label
    # di depannya sebagai registrable domain.
    for index in range(1, len(labels)):
        suffix = ".".join(labels[index:])

        if suffix in _PUBLIC_SUFFIXES:
            return ".".join(labels[index - 1 :])

    return ".".join(labels[-2:])


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


def _request_is_https(request: Optional[Request]) -> bool:
    if request is None:
        return False

    if request.url.scheme == "https":
        return True

    if settings.TRUST_PROXY_HEADERS:
        forwarded_proto = request.headers.get(
            "x-forwarded-proto",
            "",
        )

        return (
            forwarded_proto.split(",")[0].strip().lower()
            == "https"
        )

    return False


def resolve_cookie_policy(request: Optional[Request] = None) -> CookiePolicy:
    """Hitung atribut cookie yang aman untuk request saat ini."""

    secure = settings.cookie_secure
    samesite = settings.COOKIE_SAMESITE

    # Browser menolak cookie Secure pada koneksi HTTP. Jika production
    # diakses tanpa HTTPS, jangan biarkan login "berhasil" di UI tetapi
    # cookie-nya dibuang browser (gejala: logout saat refresh).
    if secure and request is not None and not _request_is_https(request):
        logger.warning(
            "COOKIE_SECURE aktif tetapi request bukan HTTPS. "
            "Cookie autentikasi dikirim tanpa flag Secure agar sesi "
            "tetap berjalan. SEGERA aktifkan HTTPS untuk production. "
            "Jika TLS diterminasi reverse proxy, set "
            "TRUST_PROXY_HEADERS=true."
        )
        secure = False

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
