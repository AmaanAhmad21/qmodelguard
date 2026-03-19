"""Pytest fixtures. Ensures DB is initialized before tests."""
import os
import pytest

# High rate limits so the full suite (many register/login/upload) doesn't hit 429.
os.environ.setdefault("RATE_LIMIT_REGISTER", "1000/minute")
os.environ.setdefault("RATE_LIMIT_LOGIN", "1000/minute")
os.environ.setdefault("RATE_LIMIT_UPLOAD", "1000/minute")

from app.db.database import init_db


@pytest.fixture(scope="session", autouse=True)
def init_database():
    """Create DB tables before any tests run."""
    init_db()
