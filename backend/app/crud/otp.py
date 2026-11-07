from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from app.models import PasswordResetOTP

def get_recent(db: Session, user_id: int, now: datetime, cooldown: int) -> Optional[PasswordResetOTP]:
    return (
        db.query(PasswordResetOTP)
        .filter(
            PasswordResetOTP.user_id == user_id,
            PasswordResetOTP.created_at >= now - timedelta(seconds=cooldown)
        )
        .order_by(PasswordResetOTP.id.desc())
        .first()
    )

def get_active(db: Session, user_id: int) -> Optional[PasswordResetOTP]:
    return (
        db.query(PasswordResetOTP)
        .filter(
            PasswordResetOTP.user_id == user_id,
            PasswordResetOTP.is_used == False
        )
        .order_by(PasswordResetOTP.id.desc())
        .first()
    )

def deactivate_all(db: Session, user_id: int):
    db.query(PasswordResetOTP).filter(
        PasswordResetOTP.user_id == user_id,
        PasswordResetOTP.is_used == False
    ).update({PasswordResetOTP.is_used: True}, synchronize_session=False)
    db.commit()

def create(db: Session, user_id: int, otp_hash: str, expires_at: datetime) -> PasswordResetOTP:
    db_otp = PasswordResetOTP(
        user_id=user_id,
        otp_hash=otp_hash,
        expires_at=expires_at,
        is_used=False,
        attempts=0
    )
    db.add(db_otp)
    db.commit()
    db.refresh(db_otp)
    return db_otp

def update(db: Session, db_otp: PasswordResetOTP) -> PasswordResetOTP:
    db.commit()
    db.refresh(db_otp)
    return db_otp
