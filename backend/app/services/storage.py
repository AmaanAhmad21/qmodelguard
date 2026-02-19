"""File storage wrapper for model files.

TODO: Add proper path validation, cleanup of temp files, size limits.
"""

import os
import uuid
from pathlib import Path

BACKEND_ROOT = Path(__file__).parent.parent.parent
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", str(BACKEND_ROOT / "app" / "storage"))).resolve()


def ensure_storage_dir():
    """Create storage directory if needed."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def save_file(content: bytes, filename: str, user_id: int) -> str:
    """Save uploaded file and return storage path.
    TODO: Sanitize filename, enforce size limits.
    """
    ext = Path(filename).suffix
    safe_name = f"{uuid.uuid4().hex}{ext}"
    user_dir = STORAGE_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    path = user_dir / safe_name
    path.write_bytes(content)
    return str(path.relative_to(BACKEND_ROOT))


def get_storage_path() -> Path:
    """Return the storage directory path."""
    return STORAGE_DIR


def load_file(storage_path: str) -> bytes:
    """Load file content by storage path."""
    full_path = BACKEND_ROOT / storage_path
    if not full_path.exists() or not full_path.is_file():
        raise FileNotFoundError(str(full_path))
    return full_path.read_bytes()


def delete_file(storage_path: str) -> None:
    """Delete file by storage path. TODO: Implement if needed."""
    full_path = BACKEND_ROOT / storage_path
    if full_path.exists():
        full_path.unlink()
