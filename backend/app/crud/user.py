from sqlalchemy.orm import Session
from typing import Optional
from app.models import User
from app.schemas import UserRegister
from app.auth import hash_password

def get_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_by_wa(db: Session, wa_candidates: list[str]) -> Optional[User]:
    return db.query(User).filter(User.no_wa.in_(wa_candidates)).first()

def get_by_wa_exclude_id(db: Session, wa_candidates: list[str], exclude_id: int) -> Optional[User]:
    return db.query(User).filter(User.no_wa.in_(wa_candidates), User.id != exclude_id).first()

def create(db: Session, user_data: UserRegister, cleaned_wa: str) -> User:
    db_user = User(
        nama=user_data.nama.strip(),
        no_wa=cleaned_wa,
        password_hash=hash_password(user_data.password),
        is_alarm_active=True,
        is_verified=False,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update(db: Session, db_user: User) -> User:
    db.commit()
    db.refresh(db_user)
    return db_user