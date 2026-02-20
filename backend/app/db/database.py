"""Database session and setup."""
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.db.models import Base

BACKEND_ROOT = Path(__file__).parent.parent.parent
DB_PATH = BACKEND_ROOT / "qmodelguard.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _migrate_keypairs():
    """Add key_type column if missing (Phase B migration)."""
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


def init_db():
    """Create DB dir if needed, then create tables."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _migrate_keypairs()


def get_db() -> Session:
    """Dependency for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
