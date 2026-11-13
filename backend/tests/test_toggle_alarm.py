"""Test endpoint PUT /user/toggle-alarm benar-benar menyimpan status ke database.

Ini mencegah regresi bug lama: tombol di dashboard hanya mengubah tampilan,
sehingga pengingat tetap terkirim walau user sudah mematikannya.

Tidak menyentuh Supabase: memakai SQLite in-memory dan override dependency.
"""

import asyncio

import httpx
import pytest
from fastapi import Depends, FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_current_user
from app.api.router import api_v1_router
from app.database import Base, get_db
from app.models import User


@pytest.fixture()
def client_and_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    seed = factory()
    seed.add(
        User(
            id=1,
            nama="Pengguna Uji",
            no_wa="6281111111111",
            password_hash="hash-palsu",
            is_alarm_active=True,
        )
    )
    seed.commit()
    seed.close()

    def override_get_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    def override_get_current_user(db: Session = Depends(get_db)) -> User:
        return db.query(User).filter(User.id == 1).first()

    app = FastAPI()
    app.include_router(api_v1_router)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield app, factory
    app.dependency_overrides.clear()


def _put(app: FastAPI, path: str, payload: dict) -> httpx.Response:
    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.put(path, json=payload)

    return asyncio.run(run())


def test_toggle_alarm_persists_false(client_and_factory):
    app, factory = client_and_factory

    response = _put(app, "/api/v1/user/toggle-alarm", {"is_alarm_active": False})

    assert response.status_code == 200
    assert response.json()["is_alarm_active"] is False

    db = factory()
    try:
        assert db.query(User).filter(User.id == 1).first().is_alarm_active is False
    finally:
        db.close()


def test_toggle_alarm_can_be_reenabled(client_and_factory):
    app, factory = client_and_factory

    assert _put(app, "/api/v1/user/toggle-alarm", {"is_alarm_active": False}).status_code == 200
    response = _put(app, "/api/v1/user/toggle-alarm", {"is_alarm_active": True})

    assert response.status_code == 200
    assert response.json()["is_alarm_active"] is True

    db = factory()
    try:
        assert db.query(User).filter(User.id == 1).first().is_alarm_active is True
    finally:
        db.close()


def test_toggle_alarm_rejects_invalid_payload(client_and_factory):
    app, _ = client_and_factory

    response = _put(app, "/api/v1/user/toggle-alarm", {"is_alarm_active": "bukan-boolean"})

    assert response.status_code == 422
