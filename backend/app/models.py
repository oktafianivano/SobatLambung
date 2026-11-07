from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nama = Column(String(100), nullable=False)
    no_wa = Column(String(20), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_alarm_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, nama='{self.nama}', no_wa='{self.no_wa}', is_alarm_active={self.is_alarm_active})>"


class PasswordResetOTP(Base):
    __tablename__ = "password_reset_otps"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    otp_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    def __repr__(self):
        return f"<PasswordResetOTP(id={self.id}, user_id={self.user_id}, is_used={self.is_used})>"
