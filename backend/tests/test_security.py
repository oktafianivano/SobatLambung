"""Test lapisan keamanan Sobat Lambung.

Mencakup: sanitasi input, masking nomor, hardening JWT, guard bcrypt,
security headers, rate limiting, audit log admin, dan keberadaan RLS pada
file migrasi.

Catatan: test ini TIDAK memakai database Supabase. Dipakai SQLite in-memory
agar cepat dan tidak butuh kredensial (aman untuk CI).
"""

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
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    test_app = FastAPI()
    test_app.state.limiter = limiter
    test_app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    test_app.add_middleware(SecurityHeadersMiddleware)
    test_app.include_router(api_v1_router)
    test_app.dependency_overrides[get_db] = override_get_db

    # Rate limit global dimatikan selama test fungsional supaya tidak saling
    # memblokir. Test rate limit memakai app+limiter sendiri di bawah.
    previous = limiter.enabled
    limiter.enabled = False
    try:
        with TestClient(test_app) as c:
            yield c
    finally:
        limiter.enabled = previous
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _register(client, nama="Rizky Pratama", no_wa="081234567890", password="rahasia123"):
    return client.post(
        "/api/v1/auth/register",
        json={"nama": nama, "no_wa": no_wa, "password": password},
    )


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
    client = TestClient(_header_app())
    response = client.get("/health", headers={"x-forwarded-proto": "https"})
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
# 6. Alur auth via API
# --------------------------------------------------------------------------- #
def test_register_returns_token_and_masked_phone(client):
    response = _register(client)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["no_wa_masked"] == "6281*****7890"
    assert "password_hash" not in body["user"]


def test_register_rejects_xss_name(client):
    response = _register(client, nama="<script>alert(1)</script>")
    assert response.status_code == 400
    assert isinstance(response.json()["detail"], str)


def test_register_rejects_duplicate_phone(client):
    assert _register(client).status_code == 201
    duplicate = _register(client, nama="Orang Lain")
    assert duplicate.status_code == 400


def test_login_profile_and_short_password(client):
    assert _register(client).status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"no_wa": "081234567890", "password": "rahasia123"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    profile = client.get(
        "/api/v1/user/profile", headers={"Authorization": f"Bearer {token}"}
    )
    assert profile.status_code == 200
    assert profile.json()["no_wa_masked"] == "6281*****7890"

    bad = client.post(
        "/api/v1/auth/login",
        json={"no_wa": "081234567890", "password": "salah"},
    )
    assert bad.status_code == 401

    too_long = client.post(
        "/api/v1/auth/register",
        json={"nama": "Budi", "no_wa": "081234567891", "password": "a" * 73},
    )
    assert too_long.status_code == 422


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
