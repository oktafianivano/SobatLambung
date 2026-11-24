
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    text,
)
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    nama = Column(
        String(100),
        nullable=False,
    )

    no_wa = Column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    is_alarm_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    # WhatsApp verification
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        server_default=text("false"),
    )

    verified_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )

    def __repr__(self):
        return (
            f"<User(id={self.id}, "
            f"nama='{self.nama}', "
            f"is_verified={self.is_verified}, "
            f"is_alarm_active={self.is_alarm_active})>"
        )


class PasswordResetOTP(Base):
    __tablename__ = "password_reset_otps"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    otp_hash = Column(
        String(255),
        nullable=False,
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    is_used = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    attempts = Column(
        Integer,
        default=0,
        nullable=False,
    )

    # reset: password recovery
    # verify: WhatsApp number verification
    purpose = Column(
        String(20),
        nullable=False,
        default="reset",
        server_default="reset",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )

    def __repr__(self):
        return (
            f"<PasswordResetOTP(id={self.id}, "
            f"user_id={self.user_id}, "
            f"purpose='{self.purpose}', "
            f"is_used={self.is_used}, "
            f"attempts={self.attempts})>"
        )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    actor = Column(
        String(100),
        nullable=False,
        default="admin",
    )

    action = Column(
        String(50),
        nullable=False,
        index=True,
    )

    target_type = Column(
        String(50),
        nullable=False,
        default="user",
    )

    target_id = Column(
        Integer,
        nullable=True,
        index=True,
    )

    detail = Column(
        String(500),
        nullable=True,
    )

    ip_address = Column(
        String(45),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    def __repr__(self):
        return (
            f"<AuditLog(id={self.id}, "
            f"action='{self.action}', "
            f"target={self.target_type}:{self.target_id})>"
        )
