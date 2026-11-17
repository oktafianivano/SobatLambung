"""Test konfigurasi migrasi (tanpa koneksi database).

Memastikan Alembic terpasang dengan benar, hanya ada satu head, dan model
SQLAlchemy memuat tabel yang diharapkan.
"""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from app import models  # noqa: F401  -> registrasi model ke metadata
from app.database import Base

BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_models_metadata_contains_expected_tables():
    assert {"users", "password_reset_otps"} <= set(Base.metadata.tables.keys())


def test_alembic_has_exactly_one_head():
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    assert len(heads) == 1
    assert script.get_current_head() == heads[0]


def test_baseline_revision_is_reachable_from_base():
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    revisions = list(script.walk_revisions())
    assert revisions, "minimal satu revisi migrasi harus ada"
    assert revisions[-1].down_revision is None
