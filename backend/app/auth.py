from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import jwt
import bcrypt
from app.config import settings

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


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
    to_encode.update({"exp": now + expires_delta, "iat": now, "type": token_type})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


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


def _decode_token(token: str, expected_type: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        return payload
    except jwt.PyJWTError:
        return None


def decode_access_token(token: str) -> Optional[dict]:
    return _decode_token(token, ACCESS_TOKEN_TYPE)


def decode_refresh_token(token: str) -> Optional[dict]:
    return _decode_token(token, REFRESH_TOKEN_TYPE)
