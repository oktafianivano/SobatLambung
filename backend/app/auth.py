from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import secrets
import jwt
import bcrypt
from app.config import settings

# Batas keras bcrypt 5.x: password > 72 byte melempar ValueError.
BCRYPT_MAX_PASSWORD_BYTES = 72

TOKEN_TYPE_ACCESS = "access"
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


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Buat JWT dengan klaim keamanan lengkap.

    - ``iat``/``nbf``: waktu terbit & mulai berlaku.
    - ``exp``: kedaluwarsa (default dari settings, 12 jam).
    - ``jti``: ID unik token (memudahkan audit/revoke di masa depan).
    - ``typ``: penanda bahwa token ini access token, bukan token lain.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = data.copy()
    to_encode.update(
        {
            "iat": now,
            "nbf": now,
            "exp": expire,
            "jti": secrets.token_urlsafe(16),
            "typ": TOKEN_TYPE_ACCESS,
        }
    )
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:

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
    if token_type is not None and token_type != TOKEN_TYPE_ACCESS:
        return None

    if "sub" not in payload:
        return None

    return payload
