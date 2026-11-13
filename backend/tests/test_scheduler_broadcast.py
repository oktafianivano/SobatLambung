"""Test perilaku broadcast: pengingat HANYA dikirim ke user yang aktif.

Menggunakan SQLite in-memory dan meng-*mock* pengiriman Fonnte, jadi tidak
ada koneksi ke Supabase maupun WhatsApp sungguhan.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import scheduler as scheduler_module
from app.database import Base
from app.models import User


@pytest.fixture()
def sqlite_session_factory(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    monkeypatch.setattr(scheduler_module, "SessionLocal", factory)
    return factory


@pytest.fixture()
def sent_messages(monkeypatch):
    sent: list[tuple[str, str]] = []

    async def fake_send(target_wa: str, message: str) -> dict:
        sent.append((target_wa, message))
        return {"status": True}

    monkeypatch.setattr(scheduler_module, "send_fonnte_message", fake_send)
    return sent


def _seed_users(factory, rows):
    session = factory()
    session.add_all(
        [
            User(
                nama=nama,
                no_wa=no_wa,
                password_hash="hash-palsu",
                is_alarm_active=aktif,
            )
            for nama, no_wa, aktif in rows
        ]
    )
    session.commit()
    session.close()


def test_broadcast_only_sends_to_active_users(sqlite_session_factory, sent_messages):
    _seed_users(
        sqlite_session_factory,
        [
            ("User Aktif", "6281111111111", True),
            ("User Nonaktif", "6282222222222", False),
        ],
    )

    scheduler_module.trigger_scheduled_broadcast("lunch")

    targets = [target for target, _ in sent_messages]
    assert targets == ["6281111111111"]


def test_broadcast_sends_nothing_when_all_users_inactive(sqlite_session_factory, sent_messages):
    _seed_users(
        sqlite_session_factory,
        [
            ("Nonaktif A", "6283333333333", False),
            ("Nonaktif B", "6284444444444", False),
        ],
    )

    scheduler_module.trigger_scheduled_broadcast("dinner")

    assert sent_messages == []


def test_broadcast_message_contains_user_name(sqlite_session_factory, sent_messages):
    _seed_users(sqlite_session_factory, [("Dimas", "6285555555555", True)])

    scheduler_module.trigger_scheduled_broadcast("breakfast")

    assert len(sent_messages) == 1
    _, message = sent_messages[0]
    assert "Dimas" in message
