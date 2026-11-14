from typing import Optional
from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.utils import mask_phone, sanitize_person_name, sanitize_phone_input

# bcrypt 5.x menolak password > 72 byte (bukan karakter). Batasi sejak schema
# agar user mendapat pesan yang jelas, bukan error 500 dari library.
PASSWORD_MAX_BYTES = 72
PASSWORD_MIN_LENGTH = 6


def _validate_password(value: str, field_label: str = "Kata sandi") -> str:
    if len(value) < PASSWORD_MIN_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_label} minimal {PASSWORD_MIN_LENGTH} karakter.",
        )
    if len(value.encode("utf-8")) > PASSWORD_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_label} terlalu panjang (maksimal {PASSWORD_MAX_BYTES} byte).",
        )
    return value


class UserRegister(BaseModel):
    nama: str = Field(..., min_length=2, max_length=100, description="Nama lengkap mahasiswa")
    no_wa: str = Field(..., min_length=9, max_length=20, description="Nomor WhatsApp (contoh: 08123456789 atau 628123456789)")
    password: str = Field(..., min_length=PASSWORD_MIN_LENGTH, description="Kata sandi minimal 6 karakter")

    @field_validator("nama", mode="before")
    @classmethod
    def _clean_nama(cls, value):
        return sanitize_person_name(value, field_label="Nama lengkap")

    @field_validator("no_wa", mode="before")
    @classmethod
    def _clean_no_wa(cls, value):
        return sanitize_phone_input(value)

    @field_validator("password")
    @classmethod
    def _clean_password(cls, value):
        return _validate_password(value)


class UserLogin(BaseModel):
    no_wa: str = Field(..., description="Nomor WhatsApp terdaftar")
    password: str = Field(..., description="Kata sandi akun")

    @field_validator("no_wa", mode="before")
    @classmethod
    def _clean_no_wa(cls, value):
        return sanitize_phone_input(value)


class UserResponse(BaseModel):
    id: int
    nama: str
    no_wa: str
    is_alarm_active: bool

    model_config = ConfigDict(from_attributes=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def no_wa_masked(self) -> str:
        """Nomor tersamarkan untuk ditampilkan di UI (privasi)."""
        return mask_phone(self.no_wa)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ToggleAlarmRequest(BaseModel):
    is_alarm_active: bool


class ForgotPasswordRequest(BaseModel):
    no_wa: str = Field(..., description="Nomor WhatsApp terdaftar yang akan menerima kode OTP")

    @field_validator("no_wa", mode="before")
    @classmethod
    def _clean_no_wa(cls, value):
        return sanitize_phone_input(value)


class ResetPasswordRequest(BaseModel):
    no_wa: str = Field(..., description="Nomor WhatsApp terdaftar")
    otp: str = Field(..., min_length=6, max_length=6, description="Kode OTP 6 digit dari WhatsApp")
    new_password: str = Field(..., min_length=PASSWORD_MIN_LENGTH, description="Kata sandi baru minimal 6 karakter")

    @field_validator("no_wa", mode="before")
    @classmethod
    def _clean_no_wa(cls, value):
        return sanitize_phone_input(value)

    @field_validator("otp")
    @classmethod
    def _validate_otp(cls, value):
        cleaned = value.strip()
        if not cleaned.isdigit() or len(cleaned) != 6:
            raise ValueError("Kode OTP harus terdiri dari tepat 6 angka.")
        return cleaned

    @field_validator("new_password")
    @classmethod
    def _clean_password(cls, value):
        return _validate_password(value, field_label="Kata sandi baru")


class UpdateProfileRequest(BaseModel):
    nama: str = Field(..., min_length=2, max_length=100, description="Nama lengkap mahasiswa")
    no_wa: str = Field(..., min_length=9, max_length=20, description="Nomor WhatsApp aktif")
    current_password: str = Field(..., min_length=1, description="Kata sandi saat ini sebagai konfirmasi")

    @field_validator("nama", mode="before")
    @classmethod
    def _clean_nama(cls, value):
        return sanitize_person_name(value, field_label="Nama lengkap")

    @field_validator("no_wa", mode="before")
    @classmethod
    def _clean_no_wa(cls, value):
        return sanitize_phone_input(value)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, description="Kata sandi saat ini")
    new_password: str = Field(..., min_length=PASSWORD_MIN_LENGTH, description="Kata sandi baru minimal 6 karakter")

    @field_validator("new_password")
    @classmethod
    def _clean_password(cls, value):
        return _validate_password(value, field_label="Kata sandi baru")


class AdminUserCreate(BaseModel):
    """Payload admin untuk membuat user manual (wajib punya password)."""

    nama: str = Field(..., min_length=2, max_length=100)
    no_wa: str = Field(..., min_length=9, max_length=20)
    password: str = Field(..., min_length=PASSWORD_MIN_LENGTH)
    is_alarm_active: Optional[bool] = True

    @field_validator("nama", mode="before")
    @classmethod
    def _clean_nama(cls, value):
        return sanitize_person_name(value, field_label="Nama lengkap")

    @field_validator("no_wa", mode="before")
    @classmethod
    def _clean_no_wa(cls, value):
        return sanitize_phone_input(value)

    @field_validator("password")
    @classmethod
    def _clean_password(cls, value):
        return _validate_password(value)


class AdminUserUpdate(BaseModel):
    """Semua field opsional; hanya yang dikirim yang akan diubah."""

    nama: Optional[str] = Field(default=None, min_length=2, max_length=100)
    no_wa: Optional[str] = Field(default=None, min_length=9, max_length=20)
    password: Optional[str] = Field(default=None, min_length=PASSWORD_MIN_LENGTH)
    is_alarm_active: Optional[bool] = None

    @field_validator("nama", mode="before")
    @classmethod
    def _clean_nama(cls, value):
        if value is None:
            return None
        return sanitize_person_name(value, field_label="Nama lengkap")

    @field_validator("no_wa", mode="before")
    @classmethod
    def _clean_no_wa(cls, value):
        if value is None:
            return None
        return sanitize_phone_input(value)

    @field_validator("password")
    @classmethod
    def _clean_password(cls, value):
        if value is None:
            return None
        return _validate_password(value)


class AlarmMessagePreview(BaseModel):
    meal_type: str
    scheduled_time: str
    title: str
    message: str
    menu_recommendations: list[str]
    tips_lambung: str
