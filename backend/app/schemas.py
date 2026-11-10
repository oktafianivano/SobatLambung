from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class UserRegister(BaseModel):
    nama: str = Field(..., min_length=2, max_length=100, description="Nama lengkap mahasiswa")
    no_wa: str = Field(..., min_length=9, max_length=20, description="Nomor WhatsApp (contoh: 08123456789 atau 628123456789)")
    password: str = Field(..., min_length=6, description="Kata sandi minimal 6 karakter")


class UserLogin(BaseModel):
    no_wa: str = Field(..., description="Nomor WhatsApp terdaftar")
    password: str = Field(..., description="Kata sandi akun")


class UserResponse(BaseModel):
    id: int
    nama: str
    no_wa: str
    is_alarm_active: bool

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ToggleAlarmRequest(BaseModel):
    is_alarm_active: bool


class ForgotPasswordRequest(BaseModel):
    no_wa: str = Field(..., description="Nomor WhatsApp terdaftar yang akan menerima kode OTP")


class ResetPasswordRequest(BaseModel):
    no_wa: str = Field(..., description="Nomor WhatsApp terdaftar")
    otp: str = Field(..., min_length=6, max_length=6, description="Kode OTP 6 digit dari WhatsApp")
    new_password: str = Field(..., min_length=6, description="Kata sandi baru minimal 6 karakter")


class UpdateProfileRequest(BaseModel):
    nama: str = Field(..., min_length=2, max_length=100, description="Nama lengkap mahasiswa")
    no_wa: str = Field(..., min_length=9, max_length=20, description="Nomor WhatsApp aktif")
    current_password: str = Field(..., min_length=1, description="Kata sandi saat ini sebagai konfirmasi")


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, description="Kata sandi saat ini")
    new_password: str = Field(..., min_length=6, description="Kata sandi baru minimal 6 karakter")


class AlarmMessagePreview(BaseModel):
    meal_type: str
    scheduled_time: str
    title: str
    message: str
    menu_recommendations: list[str]
    tips_lambung: str
