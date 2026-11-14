from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
import secrets
from datetime import timedelta

from app.database import get_db
from app.schemas import UserRegister, UserLogin, TokenResponse, ForgotPasswordRequest, ResetPasswordRequest
from app.auth import hash_password, verify_password, create_access_token, password_fingerprint
from app.limiter import (
    LOGIN_LIMIT,
    OTP_REQUEST_LIMIT,
    OTP_RESET_LIMIT,
    REGISTER_LIMIT,
    limiter,
)
from app.utils import clean_wa, normalize_wa, get_wa_candidates, get_utcnow_naive
from app.scheduler import build_reset_otp_message, send_fonnte_message
from app.crud import user as crud_user
from app.crud import otp as crud_otp

router = APIRouter()

OTP_EXPIRE_MINUTES = 10
OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_MAX_ATTEMPTS = 5

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(REGISTER_LIMIT)
def register(request: Request, user_data: UserRegister, db: Session = Depends(get_db)):
    cleaned_wa = normalize_wa(user_data.no_wa)
    wa_candidates = get_wa_candidates(cleaned_wa)
    
    if crud_user.get_by_wa(db, wa_candidates):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nomor WhatsApp sudah terdaftar. Silakan login.")

    new_user = crud_user.create(db, user_data, cleaned_wa)

    access_token = create_access_token(
        data={"sub": str(new_user.id), "nama": new_user.nama, "pwd": password_fingerprint(new_user.password_hash)}
    )
    return {"access_token": access_token, "token_type": "bearer", "user": new_user}

@router.post("/login", response_model=TokenResponse)
@limiter.limit(LOGIN_LIMIT)
def login(request: Request, login_data: UserLogin, db: Session = Depends(get_db)):
    wa_candidates = get_wa_candidates(clean_wa(login_data.no_wa))
    user_obj = crud_user.get_by_wa(db, wa_candidates)
    
    if not user_obj or not verify_password(login_data.password, user_obj.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nomor WhatsApp atau kata sandi salah.")

    access_token = create_access_token(
        data={"sub": str(user_obj.id), "nama": user_obj.nama, "pwd": password_fingerprint(user_obj.password_hash)}
    )
    return {"access_token": access_token, "token_type": "bearer", "user": user_obj}

@router.post("/forgot-password/request")
@limiter.limit(OTP_REQUEST_LIMIT)
async def forgot_password_request(request: Request, payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    generic_response = {"success": True, "message": "Jika nomor WhatsApp terdaftar, kode OTP telah kami kirim."}

    user_obj = crud_user.get_by_wa(db, get_wa_candidates(clean_wa(payload.no_wa)))
    if not user_obj:
        return generic_response

    now = get_utcnow_naive()
    if crud_otp.get_recent(db, user_obj.id, now, OTP_RESEND_COOLDOWN_SECONDS):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"Mohon tunggu {OTP_RESEND_COOLDOWN_SECONDS} detik.")

    crud_otp.deactivate_all(db, user_obj.id)

    otp_code = f"{secrets.randbelow(1_000_000):06d}"
    crud_otp.create(db, user_obj.id, hash_password(otp_code), now + timedelta(minutes=OTP_EXPIRE_MINUTES))

    message = build_reset_otp_message(user_obj.nama, otp_code, OTP_EXPIRE_MINUTES)
    await send_fonnte_message(user_obj.no_wa, message)

    return generic_response

@router.post("/forgot-password/reset")
@limiter.limit(OTP_RESET_LIMIT)
def reset_password(request: Request, payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    invalid_detail = "Kode OTP tidak valid atau sudah kedaluwarsa. Silakan minta kode baru."

    user_obj = crud_user.get_by_wa(db, get_wa_candidates(clean_wa(payload.no_wa)))
    if not user_obj:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=invalid_detail)

    otp_record = crud_otp.get_active(db, user_obj.id)
    if not otp_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=invalid_detail)

    if otp_record.expires_at < get_utcnow_naive():
        otp_record.is_used = True
        crud_otp.update(db, otp_record)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kode OTP sudah kedaluwarsa.")

    if otp_record.attempts >= OTP_MAX_ATTEMPTS:
        otp_record.is_used = True
        crud_otp.update(db, otp_record)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Terlalu banyak percobaan salah.")

    if not verify_password(payload.otp.strip(), otp_record.otp_hash):
        otp_record.attempts += 1
        remaining = OTP_MAX_ATTEMPTS - otp_record.attempts
        if remaining <= 0:
            otp_record.is_used = True
        crud_otp.update(db, otp_record)
        
        if remaining <= 0:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Terlalu banyak percobaan salah.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Kode OTP salah. Sisa percobaan: {remaining}.")

    user_obj.password_hash = hash_password(payload.new_password)
    crud_user.update(db, user_obj)
    crud_otp.deactivate_all(db, user_obj.id)

    return {"success": True, "message": "Kata sandi berhasil diubah. Silakan login."}