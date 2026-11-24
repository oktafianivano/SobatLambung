
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import (
    UserResponse,
    ToggleAlarmRequest,
    UpdateProfileRequest,
    ChangePasswordRequest,
)
from app.api.dependencies import get_current_user
from app.auth import verify_password, hash_password
from app.limiter import NOTIFICATION_LIMIT, PROFILE_LIMIT, limiter
from app.utils import (
    normalize_wa,
    get_wa_candidates,
    sanitize_simple_text,
)
from app.scheduler import build_whatsapp_message, send_fonnte_message
from app.crud import user as crud_user
from app.crud import otp as crud_otp
from app.api.endpoints.auth import _set_auth_cookies

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
@limiter.limit(PROFILE_LIMIT)
def get_user_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.put("/toggle-alarm", response_model=UserResponse)
@limiter.limit(PROFILE_LIMIT)
def toggle_alarm(
    request: Request,
    payload: ToggleAlarmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.is_alarm_active = payload.is_alarm_active
    return crud_user.update(db, current_user)


@router.post("/test-notification")
@limiter.limit(NOTIFICATION_LIMIT)
async def test_notification(
    request: Request,
    meal_key: str = "breakfast",
    current_user: User = Depends(get_current_user),
):
    meal_key = sanitize_simple_text(
        meal_key,
        max_length=20,
        field_label="meal_key",
    )

    if not current_user.is_alarm_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alarm sedang nonaktif.",
        )

    if meal_key not in {"breakfast", "lunch", "dinner"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Jadwal makan tidak valid.",
        )

    message = build_whatsapp_message(current_user.nama, meal_key)
    result = await send_fonnte_message(current_user.no_wa, message)

    # Jangan mengembalikan nomor WA atau data internal provider.
    return {
        "success": bool(result and result.get("status") is True),
        "message": (
            "Notifikasi berhasil dikirim."
            if result and result.get("status") is True
            else "Notifikasi gagal dikirim. Silakan coba lagi."
        ),
        "meal_key": meal_key,
    }


@router.put("/profile/update", response_model=UserResponse)
@limiter.limit(PROFILE_LIMIT)
def update_user_profile(
    request: Request,
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(
        payload.current_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kata sandi saat ini salah.",
        )

    new_nama = payload.nama.strip()

    if len(new_nama) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nama lengkap minimal 2 karakter.",
        )

    new_wa = normalize_wa(payload.no_wa)

    # Nomor WA tidak boleh diganti melalui endpoint profil biasa.
    # Perubahan nomor memerlukan alur verifikasi OTP tersendiri.
    if new_wa != current_user.no_wa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Perubahan nomor WhatsApp membutuhkan verifikasi OTP. "
                "Nomor belum diubah."
            ),
        )

    current_user.nama = new_nama

    return crud_user.update(db, current_user)


@router.post("/change-password")
@limiter.limit(PROFILE_LIMIT)
def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(
        payload.current_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kata sandi saat ini salah.",
        )

    if payload.new_password == payload.current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sandi baru tidak boleh sama dengan yang lama.",
        )

    current_user.password_hash = hash_password(payload.new_password)

    crud_user.update(db, current_user)

    # Nonaktifkan seluruh OTP yang masih aktif.
    crud_otp.deactivate_all(db, current_user.id)

    # Password fingerprint berubah, sehingga JWT lama tidak berlaku lagi.
    # Buat cookie autentikasi baru untuk browser saat ini.
    csrf_token = _set_auth_cookies(
        response,
        current_user,
        request,
    )

    return {
        "success": True,
        "message": "Kata sandi berhasil diperbarui.",
        "csrf_token": csrf_token,
    }
