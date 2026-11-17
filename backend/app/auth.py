from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import secrets
import jwt
import bcrypt
from app.config import settings

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"

# Batas keras bcrypt 5.x: password > 72 byte melempar ValueError.
BCRYPT_MAX_PASSWORD_BYTES = 72
# Toleransi selisih jam antara server dan perangkat user.
CLOCK_SKEW_LEEWAY = timedelta(seconds=10)


def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(
            f"Kata sandi maksimal {BCRYPT_MAX_PASSWORD_BYTES} byte."
        )
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def password_fingerprint(hashed_password: str) -> str:
    return hashlib.sha256(hashed_password.encode("utf-8")).hexdigest()[:32]


def _create_token(data: dict, expires_delta: timedelta, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    to_encode = data.copy()
    to_encode.update(
        {
            "iat": now,
            "nbf": now,
            "exp": now + expires_delta,
            "jti": secrets.token_urlsafe(16),
            "typ": token_type,
        }
    )
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    return _create_token(
        data,
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        TOKEN_TYPE_ACCESS,
    )


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    return _create_token(
        data,
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        TOKEN_TYPE_REFRESH,
    )


def _decode_token(
    token: str,
    expected_type: str,
    allow_missing_type: bool = False,
) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub"], "verify_signature": True},
            leeway=CLOCK_SKEW_LEEWAY,
        )
    except jwt.PyJWTError:
        return None

    token_type = payload.get("typ")
    if token_type is None:
        # Token lama (sebelum ada klaim `typ`) tetap diterima sebagai access
        # token agar sesi yang sudah berjalan tidak langsung terputus.
        return payload if allow_missing_type else None
    if token_type != expected_type:
        return None

    if "sub" not in payload:
        return None

    return payload


def decode_access_token(token: str) -> Optional[dict]:
    return _decode_token(token, TOKEN_TYPE_ACCESS, allow_missing_type=True)


def decode_refresh_token(token: str) -> Optional[dict]:
    # Refresh token wajib punya klaim `typ=refresh`; token lama tanpa `typ`
    # tidak boleh dipakai untuk menukar access token baru.
    return _decode_token(token, TOKEN_TYPE_REFRESH, allow_missing_type=False)
