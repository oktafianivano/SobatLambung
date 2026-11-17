"""Konfigurasi runtime Alembic.

URL database TIDAK disimpan di `alembic.ini` (agar tidak ada kredensial di
repo). Nilainya diambil dari `app.config.settings`, sumber yang sama dengan
aplikasi FastAPI.
"""

from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context

from app import models  # noqa: F401  -> memastikan semua model terdaftar di metadata
from app.config import settings
from app.database import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    """Samakan skema driver dengan yang dipakai aplikasi (psycopg2)."""
    url = settings.DATABASE_URL
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def run_migrations_offline() -> None:
    """Mode offline: hasilkan SQL tanpa membuka koneksi database."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Mode online: jalankan migrasi langsung ke database."""
    connectable = create_engine(_database_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
