from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.crud import user as crud_user
from app.auth import decode_access_token, password_fingerprint

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Header Authorization Bearer token diperlukan")
    
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token tidak valid atau telah kedaluwarsa")
        
    user_obj = crud_user.get_by_id(db, int(payload["sub"]))
    if not user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")

    if payload.get("pwd") != password_fingerprint(user_obj.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesi login kedaluwarsa karena sandi berubah.")
        
    return user_obj