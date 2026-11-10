from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User
from app.config import settings
import logging
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger("admin_tools")
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

ADMIN_SECRET = settings.ADMIN_API_KEY

class UserAdminSchema(BaseModel):
    nama: Optional[str] = None
    no_wa: Optional[str] = None
    is_alarm_active: Optional[bool] = None

@router.post("/create", summary="Tambah user baru secara manual (Akses IT)")
def create_user(
    data: UserAdminSchema,
    x_admin_key: str = Header(...),
    db: Session = Depends(get_db)
):
    if x_admin_key != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Akses ditolak")
    
    new_user = User(nama=data.nama, no_wa=data.no_wa, is_alarm_active=data.is_alarm_active or True)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User berhasil dibuat", "user_id": new_user.id}

@router.get("/list", summary="List semua user (Akses IT)")
def list_users(
    x_admin_key: str = Header(...), 
    db: Session = Depends(get_db)
):
    if x_admin_key != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Akses ditolak")
    
    users = db.query(User).all()
    return [{"id": u.id, "nama": u.nama, "no_wa": u.no_wa, "is_alarm_active": u.is_alarm_active} for u in users]

@router.put("/update/{user_id}", summary="Update data user (Akses IT)")
def update_user(
    user_id: int,
    data: UserAdminSchema,
    x_admin_key: str = Header(...),
    db: Session = Depends(get_db)
):
    if x_admin_key != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Akses ditolak")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    
    if data.nama: user.nama = data.nama
    if data.no_wa: user.no_wa = data.no_wa
    if data.is_alarm_active is not None: user.is_alarm_active = data.is_alarm_active
    
    db.commit()
    return {"message": f"User {user_id} berhasil diupdate"}

@router.delete("/delete/{user_id}", summary="Hapus user (Akses IT)")
def delete_user_by_admin(
    user_id: int, 
    x_admin_key: str = Header(...), 
    db: Session = Depends(get_db)
):
    if x_admin_key != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Akses ditolak: Kunci Admin salah")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    
    nama_user = user.nama
    db.delete(user)
    db.commit()
    
    logger.info(f"Admin menghapus user: {nama_user} (ID: {user_id})")
    return {"message": f"User {nama_user} (ID: {user_id}) berhasil dihapus"}
