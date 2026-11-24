
import secrets
from datetime import timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

from app.schemas import (
    ForgotPasswordRequest,
    RegisterPendingResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
    UserLogin,
    UserRegister,
    VerifyRegistrationRequest,
)

from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    password_fingerprint,
    create_csrf_token,
)

from app.config import settings

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
from app.api.dependencies import verify_csrf


router = APIRouter()


# ---------------------------------------------------------
# Authentication configuration
# ---------------------------------------------------------

OTP_EXPIRE_MINUTES = 10
OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_MAX_ATTEMPTS = 5
VERIFY_RESEND_MAX_PER_HOUR = 5

ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"
CSRF_COOKIE_NAME = "csrf_token"

INVALID_REFRESH_DETAIL = (
    "Sesi login berakhir. Silakan login ulang."
)

COOKIE_SECURE = settings.cookie_secure
COOKIE_SAMESITE = settings.COOKIE_SAMESITE
COOKIE_DOMAIN = settings.COOKIE_DOMAIN


# ---------------------------------------------------------
# User serialization and token payload
# ---------------------------------------------------------

def _token_payload(user_obj: User) -> dict:
    return {
        "sub": str(user_obj.id),
        "nama": user_obj.nama,
        "pwd": password_fingerprint(
            user_obj.password_hash
        ),
    }


def _serialize_user(user_obj: User) -> dict:
    """Data user yang aman untuk dikirim ke frontend."""

    return {
        "id": user_obj.id,
        "nama": user_obj.nama,
        "no_wa": user_obj.no_wa,
        "no_wa_masked": mask_phone(user_obj.no_wa),
        "is_alarm_active": user_obj.is_alarm_active,
        "is_verified": user_obj.is_verified,
    }


def _auth_response(user_obj: User) -> dict:
    return {
        "success": True,
        "message": "Autentikasi berhasil.",
        "user": _serialize_user(user_obj),
    }


# ---------------------------------------------------------
# Cookie management
# ---------------------------------------------------------

def _set_auth_cookies(
    response: Response,
    user_obj: User,
) -> None:
    """
    Membuat access, refresh, dan signed CSRF cookie.
    Access dan refresh token tidak dapat dibaca JavaScript.
    """

    payload = _token_payload(user_obj)

    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)
    csrf_token = create_csrf_token()

    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
        domain=COOKIE_DOMAIN,
    )

    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
        domain=COOKIE_DOMAIN,
    )

    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        httponly=False,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
        domain=COOKIE_DOMAIN,
    )


def _clear_auth_cookies(response: Response) -> None:
    """Menghapus seluruh cookie autentikasi."""

    for cookie_name in (
        ACCESS_COOKIE_NAME,
        REFRESH_COOKIE_NAME,
        CSRF_COOKIE_NAME,
    ):
        response.delete_cookie(
            key=cookie_name,
            path="/",
            domain=COOKIE_DOMAIN,
            secure=COOKIE_SECURE,
            httponly=cookie_name != CSRF_COOKIE_NAME,
            samesite=COOKIE_SAMESITE,
        )


# ---------------------------------------------------------
# OTP helpers
# ---------------------------------------------------------

def _issue_otp(
    db: Session,
    user_id: int,
    purpose: str,
) -> str:
    """Buat OTP baru dan nonaktifkan OTP sebelumnya."""

    now = get_utcnow_naive()

    crud_otp.deactivate_all(
        db,
        user_id,
        purpose=purpose,
    )

    otp_code = f"{secrets.randbelow(1_000_000):06d}"

    crud_otp.create(
        db,
        user_id,
        hash_password(otp_code),
        now + timedelta(minutes=OTP_EXPIRE_MINUTES),
        purpose=purpose,
    )

    return otp_code


async def _send_verification_otp(
    db: Session,
    user_obj: User,
) -> None:
    otp_code = _issue_otp(
        db,
        user_obj.id,
        crud_otp.PURPOSE_VERIFY,
    )

    message = build_verification_otp_message(
        user_obj.nama,
        otp_code,
        OTP_EXPIRE_MINUTES,
    )

    await send_fonnte_message(
        user_obj.no_wa,
        message,
    )


def _validate_otp(
    db: Session,
    user_obj: User,
    otp_code: str,
    purpose: str,
):
    """Memeriksa OTP, masa berlaku, dan jumlah percobaan."""

    invalid_detail = (
        "Kode OTP tidak valid atau sudah kedaluwarsa. "
        "Silakan minta kode baru."
    )

    otp_record = crud_otp.get_active(
        db,
        user_obj.id,
        purpose=purpose,
    )

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=invalid_detail,
        )

    now = get_utcnow_naive()

    if as_naive_utc(otp_record.expires_at) < as_naive_utc(now):
        otp_record.is_used = True
        crud_otp.update(db, otp_record)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Kode OTP sudah kedaluwarsa. "
                "Silakan minta kode baru."
            ),
        )

    if otp_record.attempts >= OTP_MAX_ATTEMPTS:
        otp_record.is_used = True
        crud_otp.update(db, otp_record)

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Terlalu banyak percobaan salah. "
                "Silakan minta kode baru."
            ),
        )

    if not verify_password(
        otp_code,
        otp_record.otp_hash,
    ):
        otp_record.attempts += 1

        remaining = OTP_MAX_ATTEMPTS - otp_record.attempts

        if remaining <= 0:
            otp_record.is_used = True

        crud_otp.update(db, otp_record)

        if remaining <= 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Terlalu banyak percobaan salah. "
                    "Silakan minta kode baru."
                ),
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Kode OTP salah. Sisa percobaan: {remaining}."
            ),
        )

    otp_record.is_used = True
    crud_otp.update(db, otp_record)

    return now


# ---------------------------------------------------------
# Registration
# ---------------------------------------------------------

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

    existing = crud_user.get_by_wa(
        db,
        get_wa_candidates(cleaned_wa),
    )

    if existing and existing.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Nomor WhatsApp sudah terdaftar. "
                "Silakan login."
            ),
        )

    if existing:
        existing.nama = user_data.nama
        existing.password_hash = hash_password(
            user_data.password
        )

        user_obj = crud_user.update(
            db,
            existing,
        )

    else:
        user_obj = crud_user.create(
            db,
            user_data,
            cleaned_wa,
        )

    await _send_verification_otp(
        db,
        user_obj,
    )

    return RegisterPendingResponse(
        no_wa_masked=mask_phone(user_obj.no_wa),
        message=(
            "Kode OTP 6 digit telah dikirim ke WhatsApp Anda. "
            "Masukkan kode tersebut untuk mengaktifkan akun."
        ),
        expires_in_seconds=OTP_EXPIRE_MINUTES * 60,
    )


@router.post("/register/verify")
@limiter.limit(OTP_RESET_LIMIT)
def verify_registration(
    request: Request,
    payload: VerifyRegistrationRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    user_obj = crud_user.get_by_wa(
        db,
        get_wa_candidates(
            clean_wa(payload.no_wa)
        ),
    )

    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Kode OTP tidak valid atau sudah kedaluwarsa. "
                "Silakan minta kode baru."
            ),
        )

    if user_obj.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Nomor WhatsApp sudah terverifikasi. "
                "Silakan login."
            ),
        )

    now = _validate_otp(
        db,
        user_obj,
        payload.otp,
        crud_otp.PURPOSE_VERIFY,
    )

    user_obj.is_verified = True
    user_obj.verified_at = now

    crud_user.update(
        db,
        user_obj,
    )

    _set_auth_cookies(
        response,
        user_obj,
    )

    return _auth_response(user_obj)


# ---------------------------------------------------------
# Refresh token
# ---------------------------------------------------------

@router.post("/refresh")
def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Memperbarui access dan refresh cookie menggunakan
    refresh JWT yang masih berlaku.

    Refresh JWT bersifat stateless. Rotasi menerbitkan token
    baru, tetapi tidak mencabut token lama yang telah dicuri.
    """

    verify_csrf(request)

    refresh_token = request.cookies.get(
        REFRESH_COOKIE_NAME
    )

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_REFRESH_DETAIL,
        )

    token_data = decode_refresh_token(
        refresh_token
    )

    if not token_data or not token_data.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_REFRESH_DETAIL,
        )

    try:
        user_id = int(token_data["sub"])
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_REFRESH_DETAIL,
        )

    user_obj = crud_user.get_by_id(
        db,
        user_id,
    )

    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_REFRESH_DETAIL,
        )

    token_fingerprint = str(
        token_data.get("pwd", "")
    )

    current_fingerprint = password_fingerprint(
        user_obj.password_hash
    )

    if not secrets.compare_digest(
        token_fingerprint,
        current_fingerprint,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_REFRESH_DETAIL,
        )

    _set_auth_cookies(
        response,
        user_obj,
    )

    return {
        "success": True,
        "message": "Sesi berhasil diperbarui.",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


# ---------------------------------------------------------
# Logout
# ---------------------------------------------------------

@router.post("/logout")
def logout(
    request: Request,
    response: Response,
):
    """Logout dengan menghapus cookie autentikasi."""

    verify_csrf(request)

    _clear_auth_cookies(response)

    return {
        "success": True,
        "message": "Berhasil logout.",
    }


# ---------------------------------------------------------
# Resend registration OTP
# ---------------------------------------------------------

@router.post("/register/resend")
@limiter.limit(OTP_REQUEST_LIMIT)
async def resend_registration_otp(
    request: Request,
    payload: ResendVerificationRequest,
    db: Session = Depends(get_db),
):
    generic_response = {
        "success": True,
        "message": (
            "Jika nomor terdaftar dan belum diverifikasi, "
            "kode OTP baru telah dikirim."
        ),
    }

    user_obj = crud_user.get_by_wa(
        db,
        get_wa_candidates(
            clean_wa(payload.no_wa)
        ),
    )

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
            detail=(
                f"Mohon tunggu {OTP_RESEND_COOLDOWN_SECONDS} "
                "detik sebelum meminta kode baru."
            ),
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
            detail=(
                "Terlalu banyak permintaan kode. "
                "Coba lagi dalam 1 jam."
            ),
        )

    await _send_verification_otp(
        db,
        user_obj,
    )

    return generic_response


# ---------------------------------------------------------
# Login
# ---------------------------------------------------------

@router.post("/login")
@limiter.limit(LOGIN_LIMIT)
def login(
    request: Request,
    login_data: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
):
    user_obj = crud_user.get_by_wa(
        db,
        get_wa_candidates(
            clean_wa(login_data.no_wa)
        ),
    )

    if not user_obj or not verify_password(
        login_data.password,
        user_obj.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nomor WhatsApp atau kata sandi salah.",
        )

    if not user_obj.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Nomor WhatsApp belum diverifikasi. "
                "Masukkan kode OTP yang dikirim saat pendaftaran, "
                "atau minta kode baru."
            ),
        )

    _set_auth_cookies(
        response,
        user_obj,
    )

    return _auth_response(user_obj)


# ---------------------------------------------------------
# Forgot password request
# ---------------------------------------------------------

@router.post("/forgot-password/request")
@limiter.limit(OTP_REQUEST_LIMIT)
async def forgot_password_request(
    request: Request,
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    generic_response = {
        "success": True,
        "message": (
            "Jika nomor WhatsApp terdaftar, "
            "kode OTP telah kami kirim."
        ),
    }

    user_obj = crud_user.get_by_wa(
        db,
        get_wa_candidates(
            clean_wa(payload.no_wa)
        ),
    )

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
            detail=(
                f"Mohon tunggu {OTP_RESEND_COOLDOWN_SECONDS} detik."
            ),
        )

    otp_code = _issue_otp(
        db,
        user_obj.id,
        crud_otp.PURPOSE_RESET,
    )

    message = build_reset_otp_message(
        user_obj.nama,
        otp_code,
        OTP_EXPIRE_MINUTES,
    )

    await send_fonnte_message(
        user_obj.no_wa,
        message,
    )

    return generic_response


# ---------------------------------------------------------
# Forgot password reset
# ---------------------------------------------------------

@router.post("/forgot-password/reset")
@limiter.limit(OTP_RESET_LIMIT)
def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    user_obj = crud_user.get_by_wa(
        db,
        get_wa_candidates(
            clean_wa(payload.no_wa)
        ),
    )

    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Kode OTP tidak valid atau sudah kedaluwarsa. "
                "Silakan minta kode baru."
            ),
        )

    _validate_otp(
        db,
        user_obj,
        payload.otp,
        crud_otp.PURPOSE_RESET,
    )

    user_obj.password_hash = hash_password(
        payload.new_password
    )

    crud_user.update(
        db,
        user_obj,
    )

    crud_otp.deactivate_all(
        db,
        user_obj.id,
    )

    _clear_auth_cookies(response)

    return {
        "success": True,
        "message": (
            "Kata sandi berhasil diubah. "
            "Silakan login kembali."
        ),
    }
