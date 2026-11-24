from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import jwt
import bcrypt
import hmac
import secrets
import uuid
from app.config import settings

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

def create_csrf_token() -> str:
    """
    Membuat signed CSRF token menggunakan HMAC-SHA256.
    Format: random_nonce.signature
    """
    nonce = secrets.token_urlsafe(32)

    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        nonce.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"{nonce}.{signature}"


def verify_csrf_token(token: str) -> bool:
    """
    Memverifikasi signature CSRF token secara constant-time.
    """
    if not isinstance(token, str) or "." not in token:
        return False

    nonce, signature = token.rsplit(".", 1)

    if not nonce or not signature:
        return False

    expected_signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        nonce.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        signature,
        expected_signature,
    )

def hash_password(password: str) -> str:
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
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    to_encode.update({
        "exp": now + expires_delta,
        "iat": now,
        "nbf": now,
        "typ": token_type,
        "type": token_type,
        "jti": str(uuid.uuid4()),
    })

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def _decode_token(token: str, expected_type: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        typ = payload.get("typ")
        legacy_type = payload.get("type")

        # Tolak jika kedua claim tipe saling bertentangan.
        if typ is not None and legacy_type is not None:
            if typ != legacy_type:
                return None

        actual_type = typ or legacy_type

        # Kompatibilitas token lama:
        # hanya access token legacy dengan password fingerprint.
        if actual_type is None:
            if expected_type != ACCESS_TOKEN_TYPE:
                return None

            if not isinstance(payload.get("pwd"), str):
                return None

            if not payload["pwd"]:
                return None

            return payload

        # Pastikan tipe token sesuai tujuan.
        if actual_type != expected_type:
            return None

        # Token baru wajib memiliki JTI.
        if not payload.get("jti"):
            return None

        return payload

    except (jwt.PyJWTError, TypeError, ValueError):
        return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    return _create_token(
        data,
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        ACCESS_TOKEN_TYPE,
    )


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    return _create_token(
        data,
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        REFRESH_TOKEN_TYPE,
    )

def decode_access_token(token: str) -> Optional[dict]:
    return _decode_token(token, ACCESS_TOKEN_TYPE)


def decode_refresh_token(token: str) -> Optional[dict]:
    return _decode_token(token, REFRESH_TOKEN_TYPE)

