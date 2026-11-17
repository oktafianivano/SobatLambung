"""Endpoint Admin Tools (khusus tim IT).

Perbaikan keamanan dibanding versi lama:
- Kunci admin dibandingkan dengan ``secrets.compare_digest`` (anti timing attack).
- User baru WAJIB punya password (sebelumnya kolom ``password_hash`` NOT NULL
  sehingga pembuatan user gagal).
- Input nama & nomor WhatsApp disanitasi sebelum disimpan.
- Nomor WhatsApp di daftar user ditampilkan dalam bentuk tersamarkan.
- Setiap create/update/delete dicatat ke tabel ``audit_logs``.
- Semua endpoint dibatasi rate limit (``ADMIN_LIMIT``).
"""

import logging
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.config import settings
from app.crud import audit as crud_audit
from app.crud import user as crud_user
from app.database import get_db
from app.limiter import ADMIN_LIMIT, limiter
from app.models import User
from app.schemas import AdminUserCreate, AdminUserUpdate
from app.utils import get_utcnow_naive, get_wa_candidates, mask_phone, normalize_wa

logger = logging.getLogger("admin_tools")
router = APIRouter()

ADMIN_SECRET = settings.ADMIN_API_KEY

def require_admin(
    x_admin_key: str = Header(..., alias="x-admin-key"),
) -> str:
    provided = x_admin_key.encode("utf-8")
    expected = ADMIN_SECRET.encode("utf-8")
    if not ADMIN_SECRET or not secrets.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak: kunci admin salah.",
        )
    return "admin"


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:45]
    return (request.client.host if request.client else "unknown")[:45]


def _serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "nama": user.nama,
        "no_wa_masked": mask_phone(user.no_wa),
        "is_alarm_active": user.is_alarm_active,
        "is_verified": user.is_verified,
    }


@router.post("/create", summary="Tambah user baru secara manual (Akses IT)")
@limiter.limit(ADMIN_LIMIT)
def create_user(
    request: Request,
    data: AdminUserCreate,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    cleaned_wa = normalize_wa(data.no_wa)
    if crud_user.get_by_wa(db, get_wa_candidates(cleaned_wa)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nomor WhatsApp sudah terdaftar.",
        )

    new_user = User(
        nama=data.nama,
        no_wa=cleaned_wa,
        password_hash=hash_password(data.password),
        is_alarm_active=True if data.is_alarm_active is None else data.is_alarm_active,
        is_verified=True if data.is_verified is None else data.is_verified,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    crud_audit.record(
        db,
        actor="admin",
        action="create",
        target_type="user",
        target_id=new_user.id,
        detail=f"Membuat user '{new_user.nama}' ({mask_phone(new_user.no_wa)})",
        ip_address=_client_ip(request),
    )
    logger.info("Admin membuat user ID=%s", new_user.id)

    return {
        "message": "User berhasil dibuat",
        "user_id": new_user.id,
        "user": _serialize_user(new_user),
    }


@router.get("/list", summary="List semua user (Akses IT)")
@limiter.limit(ADMIN_LIMIT)
def list_users(
    request: Request,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    users = db.query(User).order_by(User.id.asc()).all()
    return [_serialize_user(u) for u in users]


@router.get("/audit-logs", summary="Riwayat aktivitas admin (Akses IT)")
@limiter.limit(ADMIN_LIMIT)
def list_audit_logs(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    entries = crud_audit.list_recent(db, limit=limit)
    return [
        {
            "id": entry.id,
            "actor": entry.actor,
            "action": entry.action,
            "target_type": entry.target_type,
            "target_id": entry.target_id,
            "detail": entry.detail,
            "ip_address": entry.ip_address,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
        }
        for entry in entries
    ]


@router.put("/update/{user_id}", summary="Update data user (Akses IT)")
@limiter.limit(ADMIN_LIMIT)
def update_user(
    request: Request,
    user_id: int,
    data: AdminUserUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    user = crud_user.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")

    changes: list[str] = []

    if data.nama is not None and data.nama != user.nama:
        changes.append("nama")
        user.nama = data.nama

    if data.no_wa is not None:
        cleaned_wa = normalize_wa(data.no_wa)
        if cleaned_wa != user.no_wa:
            if crud_user.get_by_wa_exclude_id(db, get_wa_candidates(cleaned_wa), user_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Nomor WhatsApp sudah dipakai akun lain.",
                )
            changes.append("no_wa")
            user.no_wa = cleaned_wa

    if data.password is not None:
        changes.append("password")
        user.password_hash = hash_password(data.password)

    if data.is_alarm_active is not None and data.is_alarm_active != user.is_alarm_active:
        changes.append("is_alarm_active")
        user.is_alarm_active = data.is_alarm_active

    if data.is_verified is not None and data.is_verified != user.is_verified:
        changes.append("is_verified")
        user.is_verified = data.is_verified
        if data.is_verified and user.verified_at is None:
            user.verified_at = get_utcnow_naive()

    if not changes:
        return {"message": f"Tidak ada perubahan pada user {user_id}", "changed": []}

    db.commit()
    db.refresh(user)

    crud_audit.record(
        db,
        actor="admin",
        action="update",
        target_type="user",
        target_id=user_id,
        detail=f"Mengubah {', '.join(changes)} pada user '{user.nama}'",
        ip_address=_client_ip(request),
    )
    logger.info("Admin mengubah user ID=%s field=%s", user_id, changes)

    return {
        "message": f"User {user_id} berhasil diupdate",
        "changed": changes,
        "user": _serialize_user(user),
    }


@router.delete("/delete/{user_id}", summary="Hapus user (Akses IT)")
@limiter.limit(ADMIN_LIMIT)
def delete_user_by_admin(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    user = crud_user.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")

    nama_user = user.nama
    masked_wa = mask_phone(user.no_wa)
    db.delete(user)
    db.commit()

    crud_audit.record(
        db,
        actor="admin",
        action="delete",
        target_type="user",
        target_id=user_id,
        detail=f"Menghapus user '{nama_user}' ({masked_wa})",
        ip_address=_client_ip(request),
    )
    logger.info("Admin menghapus user ID=%s", user_id)

    return {"message": f"User {nama_user} (ID: {user_id}) berhasil dihapus"}
