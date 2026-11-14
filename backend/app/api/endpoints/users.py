from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserResponse, ToggleAlarmRequest, UpdateProfileRequest, ChangePasswordRequest
from app.api.dependencies import get_current_user
from app.auth import verify_password, hash_password, create_access_token, password_fingerprint
from app.limiter import NOTIFICATION_LIMIT, PROFILE_LIMIT, limiter
from app.utils import normalize_wa, get_wa_candidates, sanitize_simple_text
from app.scheduler import build_whatsapp_message, send_fonnte_message
from app.crud import user as crud_user
from app.crud import otp as crud_otp

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
    db: Session = Depends(get_db)
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
    meal_key = sanitize_simple_text(meal_key, max_length=20, field_label="meal_key")
    if not current_user.is_alarm_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Alarm sedang nonaktif.")

    msg = build_whatsapp_message(current_user.nama, meal_key)
    res = await send_fonnte_message(current_user.no_wa, msg)
    return {"success": True, "target_wa": current_user.no_wa, "meal_key": meal_key, "fonnte_result": res}

@router.put("/profile/update", response_model=UserResponse)
@limiter.limit(PROFILE_LIMIT)
def update_user_profile(
    request: Request,
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kata sandi saat ini salah.")

    # Nama sudah disanitasi oleh schema; strip sebagai lapisan kedua.
    new_nama = payload.nama.strip()
    if len(new_nama) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nama lengkap minimal 2 karakter.")

    new_wa = normalize_wa(payload.no_wa)
    if crud_user.get_by_wa_exclude_id(db, get_wa_candidates(new_wa), current_user.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nomor WhatsApp terdaftar pada akun lain.")

    current_user.nama = new_nama
    current_user.no_wa = new_wa
    return crud_user.update(db, current_user)

@router.post("/change-password")
@limiter.limit(PROFILE_LIMIT)
def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kata sandi saat ini salah.")

    if payload.new_password == payload.current_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sandi baru tidak boleh sama dengan yang lama.")

    current_user.password_hash = hash_password(payload.new_password)
    crud_user.update(db, current_user)
    crud_otp.deactivate_all(db, current_user.id)

    new_token = create_access_token(
        data={"sub": str(current_user.id), "nama": current_user.nama, "pwd": password_fingerprint(current_user.password_hash)}
    )
    return {"success": True, "message": "Kata sandi berhasil diperbarui.", "access_token": new_token, "token_type": "bearer"}
