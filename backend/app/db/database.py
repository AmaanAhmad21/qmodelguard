"""Database session and setup."""
import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.db.models import Base

BACKEND_ROOT = Path(__file__).parent.parent.parent

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    DB_PATH = BACKEND_ROOT / "qmodelguard.db"
    DATABASE_URL = f"sqlite:///{DB_PATH}"

_is_sqlite = DATABASE_URL.startswith("sqlite")
_connect_args = {"check_same_thread": False} if _is_sqlite else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _migrate_keypairs():
    """Add key_type column if missing (Phase B migration). SQLite only."""
    if not _is_sqlite:
        return
    with engine.connect() as conn:
        r = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='keypairs'"
        ))
        if r.fetchone() is None:
            return
        r = conn.execute(text("PRAGMA table_info(keypairs)"))
        cols = [row[1] for row in r]
        if "key_type" not in cols:
            conn.execute(text("ALTER TABLE keypairs ADD COLUMN key_type VARCHAR(8) DEFAULT 'kem'"))
            conn.commit()


def _migrate_models_signature():
    """Add signature_b64 and signer_id columns to models table if missing."""
    with engine.connect() as conn:
        if _is_sqlite:
            r = conn.execute(text("PRAGMA table_info(models)"))
            cols = [row[1] for row in r]
        else:
            r = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'models'"
            ))
            cols = [row[0] for row in r]
        if not cols:
            return
        if "signature_b64" not in cols:
            conn.execute(text("ALTER TABLE models ADD COLUMN signature_b64 TEXT"))
        if "signer_id" not in cols:
            conn.execute(text("ALTER TABLE models ADD COLUMN signer_id INTEGER"))
        conn.commit()


def init_db():
    """Create tables if they don't exist, run migrations."""
    if _is_sqlite:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _migrate_keypairs()
    _migrate_models_signature()


def get_db() -> Session:
    """Dependency for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
