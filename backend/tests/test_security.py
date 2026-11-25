"""Test lapisan keamanan Sobat Lambung.

Mencakup: sanitasi input, masking nomor, hardening JWT, guard bcrypt,
security headers, rate limiting, audit log admin, dan keberadaan RLS pada
file migrasi.

Catatan: test ini TIDAK memakai database Supabase. Dipakai SQLite in-memory
agar cepat dan tidak butuh kredensial (aman untuk CI).
"""

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request as StarletteRequest

from app import models  # noqa: F401  -> registrasi tabel ke metadata
from app.api.router import api_v1_router
from app.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.config import settings
from app.database import Base, get_db
from app.limiter import client_ip, limiter, rate_limit_handler
from app.middleware import SecurityHeadersMiddleware
from app.schemas import UserResponse
from app.utils import (
    mask_phone,
    sanitize_person_name,
    sanitize_phone_input,
    sanitize_simple_text,
)
from fastapi import HTTPException

BACKEND_DIR = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(
        settings,
        "ADMIN_API_KEY",
        "test-admin-key",
    )

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    test_app = FastAPI()
    test_app.state.limiter = limiter
    test_app.add_exception_handler(
        RateLimitExceeded,
        rate_limit_handler,
    )
    test_app.add_middleware(SecurityHeadersMiddleware)
    test_app.include_router(api_v1_router)
    test_app.dependency_overrides[get_db] = override_get_db

    previous = limiter.enabled
    limiter.enabled = False

    try:
        with TestClient(test_app) as c:
            yield c
    finally:
        limiter.enabled = previous
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def outbox(monkeypatch):
    """Tangkap pesan WhatsApp alih-alih mengirim OTP sungguhan."""
    messages: list[dict] = []

    async def fake_send_fonnte_message(target, message):
        messages.append({"to": target, "message": message})
        return {"status": True}

    monkeypatch.setattr(
        "app.api.endpoints.auth.send_fonnte_message", fake_send_fonnte_message
    )
    return messages


def _register(client, nama="Rizky Pratama", no_wa="081234567890", password="rahasia123"):
    return client.post(
        "/api/v1/auth/register",
        json={"nama": nama, "no_wa": no_wa, "password": password},
    )


def _last_otp(outbox):
    assert outbox, "Tidak ada pesan WhatsApp yang terkirim."
    match = re.search(r"\b(\d{6})\b", outbox[-1]["message"])
    assert match, f"Kode OTP tidak ditemukan pada pesan: {outbox[-1]['message']!r}"
    return match.group(1)


def _verify(client, no_wa, otp):
    return client.post(
        "/api/v1/auth/register/verify",
        json={"no_wa": no_wa, "otp": otp},
    )


def _register_and_verify(
    client,
    outbox,
    nama="Rizky Pratama",
    no_wa="081234567890",
    password="rahasia123",
):
    registered = _register(client, nama=nama, no_wa=no_wa, password=password)
    assert registered.status_code == 201, registered.text
    verified = _verify(client, no_wa, _last_otp(outbox))
    assert verified.status_code == 200, verified.text
    return verified.json()


# --------------------------------------------------------------------------- #
# 1. Sanitasi input (anti-XSS)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("  Rizky   Pratama ", "Rizky Pratama"),
        ("O'Brien", "O'Brien"),
        ("Aisyah-Nur", "Aisyah-Nur"),
        ("Nur Aisyah, S.Ked.", "Nur Aisyah, S.Ked."),
        ("Budi\nSantoso", "Budi Santoso"),
    ],
)
def test_sanitize_person_name_accepts_safe_names(raw, expected):
    assert sanitize_person_name(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "<script>alert('xss')</script>",
        "Budi <b>Santoso</b>",
        "Nama$Variabel",
        "Nama{json}",
        "Nama`tick`",
        "Nama\\backslash",
        "A",  # terlalu pendek
        "   ",
    ],
)
def test_sanitize_person_name_rejects_dangerous_input(raw):
    with pytest.raises(HTTPException) as exc:
        sanitize_person_name(raw)
    assert exc.value.status_code == 400


def test_sanitize_phone_input_rejects_letters_and_symbols():
    assert sanitize_phone_input(" +62 (812) 3456-7890 ") == "+62 (812) 3456-7890"
    with pytest.raises(HTTPException):
        sanitize_phone_input("0812<script>")
    with pytest.raises(HTTPException):
        sanitize_phone_input("nomor-saya")


def test_sanitize_simple_text_blocks_html():
    assert sanitize_simple_text(" breakfast ") == "breakfast"
    with pytest.raises(HTTPException):
        sanitize_simple_text("<script>")


# --------------------------------------------------------------------------- #
# 2. Masking data sensitif
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("6281234567890", "6281*****7890"),
        ("+62 812-3456-7890", "6281*****7890"),
        ("", ""),
        ("123456", "******"),
    ],
)
def test_mask_phone(raw, expected):
    assert mask_phone(raw) == expected


def test_user_response_exposes_only_masked_phone():
    class DummyUser:
        id = 1
        nama = "Rizky"
        no_wa = "6281234567890"
        is_alarm_active = True
        password_hash = "harusnya-tidak-muncul"

    data = UserResponse.model_validate(DummyUser()).model_dump()
    assert data["no_wa_masked"] == "6281*****7890"
    assert "password_hash" not in data


# --------------------------------------------------------------------------- #
# 3. Password & JWT
# --------------------------------------------------------------------------- #
def test_hash_password_rejects_over_72_bytes():
    with pytest.raises(ValueError):
        hash_password("a" * 73)
    hashed = hash_password("a" * 72)
    assert verify_password("a" * 72, hashed)


def test_access_token_has_security_claims():
    token = create_access_token({"sub": "42"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["typ"] == "access"
    assert payload["jti"]
    assert "iat" in payload and "nbf" in payload and "exp" in payload


def test_expired_token_is_rejected():
    expired = create_access_token(
        {"sub": "42"}, expires_delta=timedelta(minutes=-60)
    )
    assert decode_access_token(expired) is None


def test_tampered_token_is_rejected():
    token = create_access_token({"sub": "42"})
    tampered = token[:-3] + ("abc" if not token.endswith("abc") else "xyz")
    assert decode_access_token(tampered) is None


def test_token_signed_with_other_key_is_rejected():
    other = jwt.encode(
        {"sub": "42", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "kunci-palsu-yang-cukup-panjang-untuk-menghindari-warning-32byte",
        algorithm=settings.ALGORITHM,
    )
    assert decode_access_token(other) is None


def test_legacy_token_without_type_still_accepted():
    legacy = jwt.encode(
        {
            "sub": "7",
            "nama": "Lama",
            "pwd": "abc",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    payload = decode_access_token(legacy)
    assert payload is not None
    assert payload["sub"] == "7"


def test_token_with_wrong_type_is_rejected():
    wrong = jwt.encode(
        {
            "sub": "42",
            "typ": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    assert decode_access_token(wrong) is None


def test_token_without_subject_is_rejected():
    no_sub = jwt.encode(
        {"exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    assert decode_access_token(no_sub) is None


# --------------------------------------------------------------------------- #
# 4. Security headers
# --------------------------------------------------------------------------- #
def _header_app() -> FastAPI:
    test_app = FastAPI()
    test_app.add_middleware(SecurityHeadersMiddleware)

    @test_app.get("/health")
    def health():
        return {"status": "ok"}

    return test_app


def test_security_headers_on_api_response():
    client = TestClient(_header_app())
    response = client.get("/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "geolocation=()" in response.headers["permissions-policy"]
    assert response.headers["content-security-policy"].startswith("default-src 'none'")
    # Tanpa HTTPS, HSTS tidak boleh dikirim.
    assert "strict-transport-security" not in response.headers


def test_hsts_only_when_request_is_https():
    client = TestClient(_header_app(), base_url="https://testserver")
    response = client.get("/health")

    assert "max-age=31536000" in response.headers["strict-transport-security"]


def test_docs_csp_allows_swagger_cdn():
    client = TestClient(_header_app())
    response = client.get("/docs")
    assert "cdn.jsdelivr.net" in response.headers["content-security-policy"]


# --------------------------------------------------------------------------- #
# 5. Rate limiting
# --------------------------------------------------------------------------- #
def _make_request(headers=None, client=("192.168.1.10", 5000)):
    raw_headers = [
        (key.lower().encode(), value.encode()) for key, value in (headers or {}).items()
    ]
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": raw_headers,
        "client": client,
        "server": ("testserver", 80),
    }
    return StarletteRequest(scope)


def test_rate_limit_key_ignores_forwarded_header_by_default(monkeypatch):
    monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", False)
    request = _make_request({"x-forwarded-for": "203.0.113.9"})
    assert client_ip(request) == "192.168.1.10"


def test_rate_limit_key_uses_forwarded_header_when_trusted(monkeypatch):
    monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", True)
    request = _make_request({"x-forwarded-for": "203.0.113.9, 10.0.0.1"})
    assert client_ip(request) == "203.0.113.9"


def test_rate_limit_returns_429_with_detail_field():
    test_limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[],
        storage_uri="memory://",
        headers_enabled=False,
        enabled=True,
    )
    test_app = FastAPI()
    test_app.state.limiter = test_limiter
    test_app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

    @test_app.get("/ping")
    @test_limiter.limit("2/minute")
    def ping(request: Request):
        return {"ok": True}

    client = TestClient(test_app)
    assert client.get("/ping").status_code == 200
    assert client.get("/ping").status_code == 200
    blocked = client.get("/ping")
    assert blocked.status_code == 429
    assert "detail" in blocked.json()
    assert blocked.headers["retry-after"] == "60"


# --------------------------------------------------------------------------- #
# 6. Alur auth via API (registrasi + verifikasi OTP)
# --------------------------------------------------------------------------- #

def test_register_requires_otp_before_issuing_token(client, outbox):
    response = _register(client)

    assert response.status_code == 201, response.text

    body = response.json()
    assert body["requires_verification"] is True
    assert body["no_wa_masked"] == "6281*****7890"
    assert "access_token" not in body

    assert len(outbox) == 1
    assert re.search(r"\b\d{6}\b", outbox[0]["message"])

    verified = _verify(
        client,
        "081234567890",
        _last_otp(outbox),
    )

    assert verified.status_code == 200, verified.text

    token_body = verified.json()

    assert "access_token" not in token_body
    assert "token_type" not in token_body
    assert token_body["user"]["no_wa_masked"] == "6281*****7890"
    assert token_body["user"]["is_verified"] is True
    assert "password_hash" not in token_body["user"]

    set_cookie = verified.headers.get("set-cookie", "").lower()
    assert "httponly" in set_cookie



def test_register_rejects_xss_name(client):
    response = _register(client, nama="<script>alert(1)</script>")
    assert response.status_code == 400
    assert isinstance(response.json()["detail"], str)


def test_register_continues_for_unverified_phone(client, outbox):
    assert _register(client).status_code == 201
    # Nomor sama tapi belum diverifikasi: pendaftaran boleh diulang.
    retry = _register(client, nama="Rizky Baru")
    assert retry.status_code == 201, retry.text
    assert len(outbox) == 2

    verified = _verify(client, "081234567890", _last_otp(outbox))
    assert verified.status_code == 200
    assert verified.json()["user"]["nama"] == "Rizky Baru"

    # Setelah terverifikasi, nomor tidak boleh didaftarkan lagi.
    duplicate = _register(client, nama="Orang Lain")
    assert duplicate.status_code == 400


def test_login_rejected_until_phone_verified(client, outbox):
    assert _register(client).status_code == 201

    blocked = client.post(
        "/api/v1/auth/login",
        json={"no_wa": "081234567890", "password": "rahasia123"},
    )
    assert blocked.status_code == 403

    assert _verify(client, "081234567890", _last_otp(outbox)).status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={"no_wa": "081234567890", "password": "rahasia123"},
    )
    assert login.status_code == 200, login.text


def test_verify_rejects_wrong_otp_then_accepts_correct(client, outbox):
    assert _register(client).status_code == 201
    correct = _last_otp(outbox)
    wrong = "000000" if correct != "000000" else "111111"

    rejected = _verify(client, "081234567890", wrong)
    assert rejected.status_code == 400
    assert "Sisa percobaan" in rejected.json()["detail"]

    accepted = _verify(client, "081234567890", correct)
    assert accepted.status_code == 200


def test_resend_verification_respects_cooldown(client, outbox):
    assert _register(client).status_code == 201
    too_soon = client.post(
        "/api/v1/auth/register/resend",
        json={"no_wa": "081234567890"},
    )
    assert too_soon.status_code == 429
    assert "detik" in too_soon.json()["detail"]


def test_resend_verification_is_generic_for_unknown_number(client, outbox):
    response = client.post(
        "/api/v1/auth/register/resend",
        json={"no_wa": "081299999999"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert outbox == []


def test_login_profile_and_short_password(client, outbox):
    _register_and_verify(client, outbox)

    login = client.post(
        "/api/v1/auth/login",
        json={"no_wa": "081234567890", "password": "rahasia123"},
    )
    assert login.status_code == 200, login.text

    # Token harus diberikan melalui HttpOnly cookie, bukan JSON.
    assert "access_token" not in login.json()
    assert "httponly" in login.headers.get("set-cookie", "").lower()

    # TestClient otomatis menyimpan dan mengirim cookie.
    profile = client.get("/api/v1/user/profile")
    assert profile.status_code == 200
    assert profile.json()["no_wa_masked"] == "6281*****7890"

    bad = client.post(
        "/api/v1/auth/login",
        json={"no_wa": "081234567890", "password": "salah"},
    )
    assert bad.status_code == 401

    too_long = client.post(
        "/api/v1/auth/register",
        json={
            "nama": "Budi",
            "no_wa": "081234567891",
            "password": "a" * 73,
        },
    )
    assert too_long.status_code == 400
    assert "72 byte" in too_long.json()["detail"]


def test_profile_requires_valid_token(client):
    response = client.get("/api/v1/user/profile")
    assert response.status_code == 401


# --------------------------------------------------------------------------- #
# 7. Admin tools + audit log
# --------------------------------------------------------------------------- #
def _admin_headers():
    return {"x-admin-key": settings.ADMIN_API_KEY}


def test_admin_rejects_wrong_key(client):
    response = client.get("/api/v1/admin/list", headers={"x-admin-key": "salah"})
    assert response.status_code == 403


def test_admin_create_requires_password(client):
    response = client.post(
        "/api/v1/admin/create",
        json={"nama": "Tanpa Password", "no_wa": "081234567891"},
        headers=_admin_headers(),
    )
    assert response.status_code == 422


def test_admin_crud_writes_audit_log(client):
    created = client.post(
        "/api/v1/admin/create",
        json={
            "nama": "Budi Santoso",
            "no_wa": "081234567891",
            "password": "rahasia123",
        },
        headers=_admin_headers(),
    )
    assert created.status_code == 200, created.text
    user_id = created.json()["user_id"]

    listed = client.get("/api/v1/admin/list", headers=_admin_headers())
    assert listed.status_code == 200
    rows = listed.json()
    assert rows and rows[0]["no_wa_masked"].startswith("6281")
    assert "no_wa" not in rows[0]

    updated = client.put(
        f"/api/v1/admin/update/{user_id}",
        json={"nama": "Budi Updated", "is_alarm_active": False},
        headers=_admin_headers(),
    )
    assert updated.status_code == 200, updated.text
    assert "nama" in updated.json()["changed"]

    logs = client.get("/api/v1/admin/audit-logs", headers=_admin_headers())
    assert logs.status_code == 200
    actions = [entry["action"] for entry in logs.json()]
    assert "create" in actions
    assert "update" in actions

    deleted = client.delete(
        f"/api/v1/admin/delete/{user_id}", headers=_admin_headers()
    )
    assert deleted.status_code == 200

    logs_after = client.get("/api/v1/admin/audit-logs", headers=_admin_headers())
    assert "delete" in [entry["action"] for entry in logs_after.json()]


# --------------------------------------------------------------------------- #
# 8. Migrasi & RLS
# --------------------------------------------------------------------------- #
def test_metadata_contains_audit_logs():
    assert "audit_logs" in Base.metadata.tables


def test_migration_enables_row_level_security():
    migration = BACKEND_DIR / "alembic" / "versions" / "9f0913653886_audit_log_dan_rls.py"
    content = migration.read_text(encoding="utf-8")
    assert "ENABLE ROW LEVEL SECURITY" in content
    for table in ("users", "password_reset_otps", "audit_logs"):
        assert table in content
    # Hanya aktif untuk PostgreSQL, bukan SQLite/DB lain.
    assert "postgresql" in content


# --------------------------------------------------------------------------- #
# 9. Persistensi sesi & atribut cookie production
# --------------------------------------------------------------------------- #
def _login(client, no_wa="081234567890", password="rahasia123"):
    return client.post(
        "/api/v1/auth/login",
        json={"no_wa": no_wa, "password": password},
    )


def test_login_returns_csrf_token_in_body(client, outbox):
    _register_and_verify(client, outbox)

    login = _login(client)
    assert login.status_code == 200, login.text

    body = login.json()
    assert isinstance(body.get("csrf_token"), str)
    assert body["csrf_token"]

    # Token body harus sama dengan cookie CSRF yang di-set server.
    assert client.cookies.get("csrf_token") == body["csrf_token"]


def test_production_cookie_flags_are_secure(client, outbox, monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "COOKIE_SECURE", True)
    monkeypatch.setattr(settings, "COOKIE_SAMESITE", "auto")
    monkeypatch.setattr(settings, "COOKIE_DOMAIN", None)
    monkeypatch.setattr(settings, "COOKIE_PARTITIONED", None)
    # TestClient berjalan di HTTP; simulasi request HTTPS.
    monkeypatch.setattr(
        "app.cookies._request_is_https",
        lambda request: True,
    )

    _register_and_verify(client, outbox)
    login = _login(client)
    assert login.status_code == 200, login.text

    set_cookie = login.headers.get("set-cookie", "").lower()

    assert "secure" in set_cookie
    assert "httponly" in set_cookie
    assert "max-age=" in set_cookie
    assert "expires=" in set_cookie
    assert "samesite=lax" in set_cookie


def test_production_over_http_does_not_break_session(
    client,
    outbox,
    monkeypatch,
):
    """Cookie Secure di HTTP akan dibuang browser.

    Backend menurunkan flag Secure saat request bukan HTTPS supaya user
    tidak login lalu langsung ter-logout saat refresh. Warning tetap
    dicatat di log agar operator segera mengaktifkan HTTPS.
    """

    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "COOKIE_SECURE", True)
    monkeypatch.setattr(settings, "COOKIE_SAMESITE", "auto")
    monkeypatch.setattr(settings, "COOKIE_DOMAIN", None)
    monkeypatch.setattr(settings, "COOKIE_PARTITIONED", None)

    _register_and_verify(client, outbox)
    login = _login(client)
    assert login.status_code == 200, login.text

    set_cookie = login.headers.get("set-cookie", "").lower()
    assert "secure" not in set_cookie

    client.cookies.delete("access_token")
    profile = client.get("/api/v1/user/profile")

    assert profile.status_code == 200, profile.text
    assert client.cookies.get("access_token")


def test_cross_site_cookie_uses_samesite_none_and_partitioned(
    client,
    outbox,
    monkeypatch,
):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "COOKIE_SECURE", True)
    monkeypatch.setattr(settings, "COOKIE_SAMESITE", "auto")
    monkeypatch.setattr(settings, "COOKIE_DOMAIN", None)
    monkeypatch.setattr(settings, "COOKIE_PARTITIONED", None)
    monkeypatch.setattr(
        "app.cookies._request_is_https",
        lambda request: True,
    )

    _register_and_verify(client, outbox)

    login = client.post(
        "/api/v1/auth/login",
        json={"no_wa": "081234567890", "password": "rahasia123"},
        headers={"origin": "https://frontend.example.com"},
    )
    assert login.status_code == 200, login.text

    set_cookie = login.headers.get("set-cookie", "").lower()

    assert "samesite=none" in set_cookie
    assert "partitioned" in set_cookie
    assert "secure" in set_cookie


def test_production_trusts_forwarded_proto_for_secure_cookie(
    client,
    outbox,
    monkeypatch,
):
    """Railway/Render menerminasi TLS lalu mengirim X-Forwarded-Proto.

    Secure harus tetap aktif walau TRUST_PROXY_HEADERS tidak diset,
    supaya SameSite=None tidak diturunkan menjadi Lax.
    """

    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", False)
    monkeypatch.setattr(settings, "COOKIE_SAMESITE", "auto")
    monkeypatch.setattr(settings, "COOKIE_DOMAIN", None)
    monkeypatch.setattr(settings, "COOKIE_PARTITIONED", None)

    _register_and_verify(client, outbox)

    login = client.post(
        "/api/v1/auth/login",
        json={"no_wa": "081234567890", "password": "rahasia123"},
        headers={
            "origin": "https://frontend.example.com",
            "x-forwarded-proto": "https",
        },
    )
    assert login.status_code == 200, login.text

    set_cookie = login.headers.get("set-cookie", "").lower()

    assert "secure" in set_cookie
    assert "samesite=none" in set_cookie
    assert "partitioned" in set_cookie


def test_railway_subdomains_are_different_sites():
    """up.railway.app adalah public suffix (PSL).

    Dua service Railway pada domain *.up.railway.app adalah site berbeda,
    sehingga cookie harus SameSite=None; Lax akan diblokir browser.
    """

    from app.cookies import _registrable_site

    frontend = _registrable_site(
        "sparkling-unity-production.up.railway.app"
    )
    backend = _registrable_site(
        "sobatlambung-production.up.railway.app"
    )

    assert frontend == "sparkling-unity-production.up.railway.app"
    assert backend == "sobatlambung-production.up.railway.app"
    assert frontend != backend



def test_session_endpoint_restores_access_from_refresh_cookie(client, outbox):
    _register_and_verify(client, outbox)

    login = _login(client)
    assert login.status_code == 200, login.text

    # Simulasikan access token hilang/kedaluwarsa; refresh token tetap ada.
    client.cookies.delete("access_token")

    restored = client.get("/api/v1/auth/session")

    assert restored.status_code == 200, restored.text
    assert restored.json()["user"]["no_wa_masked"] == "6281*****7890"

    # Cookie access baru harus diterbitkan kembali.
    assert client.cookies.get("access_token")


def test_profile_auto_renews_expired_access_from_refresh(client, outbox):
    _register_and_verify(client, outbox)

    login = _login(client)
    assert login.status_code == 200, login.text

    client.cookies.delete("access_token")

    profile = client.get("/api/v1/user/profile")

    assert profile.status_code == 200, profile.text
    assert profile.json()["no_wa_masked"] == "6281*****7890"
    assert client.cookies.get("access_token")



def test_refresh_accepts_csrf_from_body_when_cookie_unreadable(
    client,
    outbox,
):
    _register_and_verify(client, outbox)

    login = _login(client)
    assert login.status_code == 200, login.text
    csrf_token = login.json()["csrf_token"]

    # Deployment beda origin: JavaScript tidak bisa membaca cookie API.
    client.cookies.delete("csrf_token")

    refreshed = client.post(
        "/api/v1/auth/refresh",
        headers={
            "x-csrf-token": csrf_token,
            "origin": "http://testserver",
        },
    )

    assert refreshed.status_code == 200, refreshed.text
    assert refreshed.json()["csrf_token"]
