"""Pencatatan audit aktivitas admin.

Dipakai oleh endpoint Admin Tools agar setiap create/update/delete punya jejak
yang bisa diperiksa manual. Kegagalan menulis audit TIDAK boleh menggagalkan
operasi utama, jadi error-nya hanya di-log.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models import AuditLog

logger = logging.getLogger("audit")


def record(
    db: Session,
    *,
    actor: str,
    action: str,
    target_type: str = "user",
    target_id: Optional[int] = None,
    detail: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Optional[AuditLog]:
    entry = AuditLog(
        actor=(actor or "admin")[:100],
        action=(action or "unknown")[:50],
        target_type=(target_type or "user")[:50],
        target_id=target_id,
        detail=(detail or None),
        ip_address=(ip_address or None),
    )
    try:
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
    except Exception:  # pragma: no cover - defensif, jangan rusak alur utama
        db.rollback()
        logger.exception("Gagal menulis audit log: action=%s target=%s", action, target_id)
        return None


def list_recent(db: Session, limit: int = 50) -> list[AuditLog]:
    safe_limit = max(1, min(limit, 200))
    return (
        db.query(AuditLog)
        .order_by(AuditLog.id.desc())
        .limit(safe_limit)
        .all()
    )
