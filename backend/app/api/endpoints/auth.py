from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
import secrets
from datetime import timedelta

from app.database import get_db
from app.models import User
from app.schemas import (
    ForgotPasswordRequest,
    RegisterPendingResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    VerifyRegistrationRequest,
)
from app.auth import hash_password, verify_password, create_access_token, password_fingerprint
from app.limiter import (
    LOGIN_LIMIT,
    OTP_REQUEST_LIMIT,
    OTP_RESET_LIMIT,
    REGISTER_LIMIT,
    limiter,
)
from app.utils import (
    as_naive_utc,
    clean_wa,
    get_utcnow_naive,
    get_wa_candidates,
    mask_phone,
    normalize_wa,
)
from app.scheduler import (
    build_reset_otp_message,
    build_verification_otp_message,
    send_fonnte_message,
)
from app.crud import user as crud_user
from app.crud import otp as crud_otp

router = APIRouter()

OTP_EXPIRE_MINUTES = 10
OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_MAX_ATTEMPTS = 5
VERIFY_RESEND_MAX_PER_HOUR = 5


def _issue_otp(db: Session, user_id: int, purpose: str) -> str:
    """Buat kode OTP baru (disimpan sebagai hash) dan nonaktifkan yang lama."""
    now = get_utcnow_naive()
    crud_otp.deactivate_all(db, user_id, purpose=purpose)
    otp_code = f"{secrets.randbelow(1_000_000):06d}"
    crud_otp.create(
        db,
        user_id,
        hash_password(otp_code),
        now + timedelta(minutes=OTP_EXPIRE_MINUTES),
        purpose=purpose,
    )
    return otp_code


async def _send_verification_otp(db: Session, user_obj: User) -> None:
    otp_code = _issue_otp(db, user_obj.id, crud_otp.PURPOSE_VERIFY)
    message = build_verification_otp_message(user_obj.nama, otp_code, OTP_EXPIRE_MINUTES)
    await send_fonnte_message(user_obj.no_wa, message)


@router.post(
    "/register",
    response_model=RegisterPendingResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(REGISTER_LIMIT)
async def register(
    request: Request,
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    cleaned_wa = normalize_wa(user_data.no_wa)
    existing = crud_user.get_by_wa(db, get_wa_candidates(cleaned_wa))

    if existing and existing.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nomor WhatsApp sudah terdaftar. Silakan login.",
        )

    if existing:
        # Pendaftaran sebelumnya belum diverifikasi: perbarui data dan kirim
        # kode baru. Nomor tetap harus dibuktikan lewat OTP.
        existing.nama = user_data.nama
        existing.password_hash = hash_password(user_data.password)
        user_obj = crud_user.update(db, existing)
    else:
        user_obj = crud_user.create(db, user_data, cleaned_wa)

    await _send_verification_otp(db, user_obj)

    return RegisterPendingResponse(
        no_wa_masked=mask_phone(user_obj.no_wa),
        message=(
            "Kode OTP 6 digit telah dikirim ke WhatsApp Anda. "
            "Masukkan kode tersebut untuk mengaktifkan akun."
        ),
        expires_in_seconds=OTP_EXPIRE_MINUTES * 60,
    )


@router.post("/register/verify", response_model=TokenResponse)
@limiter.limit(OTP_RESET_LIMIT)
def verify_registration(
    request: Request,
    payload: VerifyRegistrationRequest,
    db: Session = Depends(get_db),
):
    invalid_detail = "Kode OTP tidak valid atau sudah kedaluwarsa. Silakan minta kode baru."

    user_obj = crud_user.get_by_wa(db, get_wa_candidates(clean_wa(payload.no_wa)))
    if not user_obj:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=invalid_detail)

    if user_obj.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nomor WhatsApp sudah terverifikasi. Silakan login.",
        )

    otp_record = crud_otp.get_active(db, user_obj.id, purpose=crud_otp.PURPOSE_VERIFY)
    if not otp_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=invalid_detail)

    now = get_utcnow_naive()
    if as_naive_utc(otp_record.expires_at) < as_naive_utc(now):
        otp_record.is_used = True
        crud_otp.update(db, otp_record)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kode OTP sudah kedaluwarsa. Silakan minta kode baru.",
        )

    if otp_record.attempts >= OTP_MAX_ATTEMPTS:
        otp_record.is_used = True
        crud_otp.update(db, otp_record)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Terlalu banyak percobaan salah. Silakan minta kode baru.",
        )

    if not verify_password(payload.otp, otp_record.otp_hash):
        otp_record.attempts += 1
        remaining = OTP_MAX_ATTEMPTS - otp_record.attempts
        if remaining <= 0:
            otp_record.is_used = True
        crud_otp.update(db, otp_record)

        if remaining <= 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Terlalu banyak percobaan salah. Silakan minta kode baru.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Kode OTP salah. Sisa percobaan: {remaining}.",
        )

    user_obj.is_verified = True
    user_obj.verified_at = now
    crud_user.update(db, user_obj)
    crud_otp.deactivate_all(db, user_obj.id, purpose=crud_otp.PURPOSE_VERIFY)

    access_token = create_access_token(
        data={
            "sub": str(user_obj.id),
            "nama": user_obj.nama,
            "pwd": password_fingerprint(user_obj.password_hash),
        }
    )
    return {"access_token": access_token, "token_type": "bearer", "user": user_obj}


@router.post("/register/resend")
@limiter.limit(OTP_REQUEST_LIMIT)
async def resend_registration_otp(
    request: Request,
    payload: ResendVerificationRequest,
    db: Session = Depends(get_db),
):
    generic_response = {
        "success": True,
        "message": "Jika nomor terdaftar dan belum diverifikasi, kode OTP baru telah dikirim.",
    }

    user_obj = crud_user.get_by_wa(db, get_wa_candidates(clean_wa(payload.no_wa)))
    if not user_obj or user_obj.is_verified:
        return generic_response

    now = get_utcnow_naive()
    if crud_otp.get_recent(
        db,
        user_obj.id,
        now,
        OTP_RESEND_COOLDOWN_SECONDS,
        purpose=crud_otp.PURPOSE_VERIFY,
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Mohon tunggu {OTP_RESEND_COOLDOWN_SECONDS} detik sebelum meminta kode baru.",
        )

    if (
        crud_otp.count_since(
            db,
            user_obj.id,
            now - timedelta(hours=1),
            purpose=crud_otp.PURPOSE_VERIFY,
        )
        >= VERIFY_RESEND_MAX_PER_HOUR
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Terlalu banyak permintaan kode. Coba lagi dalam 1 jam.",
        )

    await _send_verification_otp(db, user_obj)
    return generic_response


@router.post("/login", response_model=TokenResponse)
@limiter.limit(LOGIN_LIMIT)
def login(request: Request, login_data: UserLogin, db: Session = Depends(get_db)):
    wa_candidates = get_wa_candidates(clean_wa(login_data.no_wa))
    user_obj = crud_user.get_by_wa(db, wa_candidates)

    if not user_obj or not verify_password(login_data.password, user_obj.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nomor WhatsApp atau kata sandi salah.",
        )

    # Cek verifikasi SETELAH kata sandi benar, agar tidak membocorkan status akun.
    if not user_obj.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Nomor WhatsApp belum diverifikasi. Masukkan kode OTP yang dikirim "
                "saat pendaftaran, atau minta kode baru."
            ),
        )

    access_token = create_access_token(
        data={
            "sub": str(user_obj.id),
            "nama": user_obj.nama,
            "pwd": password_fingerprint(user_obj.password_hash),
        }
    )
    return {"access_token": access_token, "token_type": "bearer", "user": user_obj}


@router.post("/forgot-password/request")
@limiter.limit(OTP_REQUEST_LIMIT)
async def forgot_password_request(
    request: Request,
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    generic_response = {"success": True, "message": "Jika nomor WhatsApp terdaftar, kode OTP telah kami kirim."}

    user_obj = crud_user.get_by_wa(db, get_wa_candidates(clean_wa(payload.no_wa)))
    if not user_obj:
        return generic_response

    now = get_utcnow_naive()
    if crud_otp.get_recent(
        db,
        user_obj.id,
        now,
        OTP_RESEND_COOLDOWN_SECONDS,
        purpose=crud_otp.PURPOSE_RESET,
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Mohon tunggu {OTP_RESEND_COOLDOWN_SECONDS} detik.",
        )

    otp_code = _issue_otp(db, user_obj.id, crud_otp.PURPOSE_RESET)
    message = build_reset_otp_message(user_obj.nama, otp_code, OTP_EXPIRE_MINUTES)
    await send_fonnte_message(user_obj.no_wa, message)

    return generic_response


@router.post("/forgot-password/reset")
@limiter.limit(OTP_RESET_LIMIT)
def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    invalid_detail = "Kode OTP tidak valid atau sudah kedaluwarsa. Silakan minta kode baru."

    user_obj = crud_user.get_by_wa(db, get_wa_candidates(clean_wa(payload.no_wa)))
    if not user_obj:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=invalid_detail)

    otp_record = crud_otp.get_active(db, user_obj.id, purpose=crud_otp.PURPOSE_RESET)
    if not otp_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=invalid_detail)

    if as_naive_utc(otp_record.expires_at) < as_naive_utc(get_utcnow_naive()):
        otp_record.is_used = True
        crud_otp.update(db, otp_record)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kode OTP sudah kedaluwarsa.")

    if otp_record.attempts >= OTP_MAX_ATTEMPTS:
        otp_record.is_used = True
        crud_otp.update(db, otp_record)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Terlalu banyak percobaan salah.")

    if not verify_password(payload.otp, otp_record.otp_hash):
        otp_record.attempts += 1
        remaining = OTP_MAX_ATTEMPTS - otp_record.attempts
        if remaining <= 0:
            otp_record.is_used = True
        crud_otp.update(db, otp_record)

        if remaining <= 0:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Terlalu banyak percobaan salah.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Kode OTP salah. Sisa percobaan: {remaining}.",
        )

    user_obj.password_hash = hash_password(payload.new_password)
    crud_user.update(db, user_obj)
    crud_otp.deactivate_all(db, user_obj.id)

    return {"success": True, "message": "Kata sandi berhasil diubah. Silakan login."}
