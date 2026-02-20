"""Pytest fixtures. Ensures DB is initialized before tests."""
import pytest

from app.db.database import init_db


@pytest.fixture(scope="session", autouse=True)
def init_database():
    """Create DB tables before any tests run."""
    init_db()
