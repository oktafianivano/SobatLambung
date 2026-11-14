from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from app.models import PasswordResetOTP

# Tujuan OTP: verifikasi nomor saat daftar, atau reset kata sandi.
PURPOSE_VERIFY = "verify"
PURPOSE_RESET = "reset"


def _base_query(db: Session, user_id: int, purpose: Optional[str]):
    query = db.query(PasswordResetOTP).filter(PasswordResetOTP.user_id == user_id)
    if purpose is not None:
        query = query.filter(PasswordResetOTP.purpose == purpose)
    return query


def get_recent(
    db: Session,
    user_id: int,
    now: datetime,
    cooldown: int,
    purpose: Optional[str] = PURPOSE_RESET,
) -> Optional[PasswordResetOTP]:
    return (
        _base_query(db, user_id, purpose)
        .filter(PasswordResetOTP.created_at >= now - timedelta(seconds=cooldown))
        .order_by(PasswordResetOTP.id.desc())
        .first()
    )


def get_active(
    db: Session,
    user_id: int,
    purpose: Optional[str] = PURPOSE_RESET,
) -> Optional[PasswordResetOTP]:
    return (
        _base_query(db, user_id, purpose)
        .filter(PasswordResetOTP.is_used == False)  # noqa: E712
        .order_by(PasswordResetOTP.id.desc())
        .first()
    )


def count_since(
    db: Session,
    user_id: int,
    since: datetime,
    purpose: Optional[str] = PURPOSE_RESET,
) -> int:
    return (
        _base_query(db, user_id, purpose)
        .filter(PasswordResetOTP.created_at >= since)
        .count()
    )


def deactivate_all(db: Session, user_id: int, purpose: Optional[str] = None):
    """Tandai OTP tidak aktif. ``purpose=None`` berarti semua tujuan."""
    (
        _base_query(db, user_id, purpose)
        .filter(PasswordResetOTP.is_used == False)  # noqa: E712
        .update({PasswordResetOTP.is_used: True}, synchronize_session=False)
    )
    db.commit()


def create(
    db: Session,
    user_id: int,
    otp_hash: str,
    expires_at: datetime,
    purpose: str = PURPOSE_RESET,
) -> PasswordResetOTP:
    db_otp = PasswordResetOTP(
        user_id=user_id,
        otp_hash=otp_hash,
        expires_at=expires_at,
        is_used=False,
        attempts=0,
        purpose=purpose,
    )
    db.add(db_otp)
    db.commit()
    db.refresh(db_otp)
    return db_otp


def update(db: Session, db_otp: PasswordResetOTP) -> PasswordResetOTP:
    db.commit()
    db.refresh(db_otp)
    return db_otp
