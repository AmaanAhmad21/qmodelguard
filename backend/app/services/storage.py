"""File storage wrapper for model files.

Path validation: all resolved paths must stay under STORAGE_DIR to prevent path traversal.
Filename: only the extension from the original filename is used; it is sanitized to safe characters.
"""

import os
import re
import uuid
from pathlib import Path

BACKEND_ROOT = Path(__file__).parent.parent.parent
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", str(BACKEND_ROOT / "app" / "storage"))).resolve()

# Extension: only alphanumeric and dot, max 20 chars (e.g. .safetensors)
_SAFE_EXT_RE = re.compile(r"^\.[a-zA-Z0-9.]{0,20}$")


def _sanitize_extension(filename: str) -> str:
    """Return a safe extension (e.g. .pt) or .bin if invalid."""
    ext = Path(filename).suffix
    if not ext or not _SAFE_EXT_RE.match(ext):
        return ".bin"
    return ext.lower()


def _resolve_storage_path(storage_path: str) -> Path:
    """Resolve storage_path relative to BACKEND_ROOT; raise if it escapes STORAGE_DIR."""
    if not storage_path or ".." in storage_path:
        raise ValueError("Invalid storage path")
    full = (BACKEND_ROOT / storage_path).resolve()
    try:
        full.relative_to(STORAGE_DIR)
    except ValueError:
        raise ValueError("Storage path escapes storage directory")
    return full


def ensure_storage_dir():
    """Create storage directory if needed."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def save_file(content: bytes, filename: str, user_id: int) -> str:
    """Save uploaded file and return storage path (relative to BACKEND_ROOT).
    Size limits are enforced by the API; only extension is taken from filename and sanitized.
    """
    ext = _sanitize_extension(filename)
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
    """Load file content by storage path. Validates path stays under STORAGE_DIR."""
    full_path = _resolve_storage_path(storage_path)
    if not full_path.exists() or not full_path.is_file():
        raise FileNotFoundError(str(full_path))
    return full_path.read_bytes()


def delete_file(storage_path: str) -> None:
    """Delete file by storage path. Validates path stays under STORAGE_DIR."""
    full_path = _resolve_storage_path(storage_path)
    if full_path.exists():
        full_path.unlink()
