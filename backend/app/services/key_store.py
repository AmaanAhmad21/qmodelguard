"""Key storage: persist and retrieve keypairs from DB.

Private keys can be encrypted at rest if KEY_ENCRYPTION_KEY is set (Fernet key, base64url).
Stored format: plain base64 (legacy) or "v2:" + base64(Fernet ciphertext) for new keys.
"""
import logging
import os
from sqlalchemy.orm import Session

from app.db.models import KeyPair
from app.services import qcrypto

logger = logging.getLogger(__name__)

_PRIV_KEY_PREFIX = "v2:"


def _get_fernet():
    """Return Fernet instance if KEY_ENCRYPTION_KEY is set, else None (store plain)."""
    key = os.getenv("KEY_ENCRYPTION_KEY", "").strip()
    if not key:
        return None
    try:
        from cryptography.fernet import Fernet
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as e:
        logger.warning("Invalid KEY_ENCRYPTION_KEY, private keys will not be encrypted: %s", e)
        return None


def _encrypt_private_key(priv_b64: str) -> str:
    """Encrypt private key for storage. Returns 'v2:' + ciphertext or plain if no key."""
    fernet = _get_fernet()
    if fernet is None:
        return priv_b64
    return _PRIV_KEY_PREFIX + fernet.encrypt(priv_b64.encode()).decode()


def _decrypt_private_key(stored: str) -> str:
    """Decrypt stored private key if v2 format, else return as-is (legacy)."""
    if not stored.startswith(_PRIV_KEY_PREFIX):
        return stored
    fernet = _get_fernet()
    if fernet is None:
        logger.warning("KEY_ENCRYPTION_KEY not set but DB has encrypted key; cannot decrypt")
        raise ValueError("Key was encrypted but KEY_ENCRYPTION_KEY is not set")
    return fernet.decrypt(stored[len(_PRIV_KEY_PREFIX):].encode()).decode()


def store_keypairs_for_user(db: Session, user_id: int) -> None:
    """Generate and store KEM + Sig keypairs for a new user."""
    kem = qcrypto.generate_kem_keypair()
    sig = qcrypto.generate_sig_keypair()
    pub_kem, priv_kem = qcrypto.keys_to_base64(kem)
    pub_sig, priv_sig = qcrypto.keys_to_base64(sig)
    _upsert(db, user_id, "kem", pub_kem, priv_kem)
    _upsert(db, user_id, "sig", pub_sig, priv_sig)


def _upsert(db: Session, user_id: int, key_type: str, pub_b64: str, priv_b64: str) -> int:
    stored_priv = _encrypt_private_key(priv_b64)
    existing = db.query(KeyPair).filter(
        KeyPair.user_id == user_id,
        KeyPair.key_type == key_type,
    ).first()
    if existing:
        existing.public_key = pub_b64
        existing.private_key = stored_priv
        db.commit()
        return existing.id
    kp = KeyPair(
        user_id=user_id,
        key_type=key_type,
        public_key=pub_b64,
        private_key=stored_priv,
    )
    db.add(kp)
    db.commit()
    db.refresh(kp)
    return kp.id


def get_user_keys(db: Session, user_id: int) -> dict | None:
    """Get kem and sig public keys for user. Returns None if no keys."""
    rows = db.query(KeyPair).filter(
        KeyPair.user_id == user_id,
        KeyPair.key_type.in_(["kem", "sig"]),
    ).all()
    if not rows:
        return None
    return {r.key_type: r for r in rows}


def get_user_public_keys(db: Session, user_id: int) -> dict | None:
    """Get public keys only. Returns {kem: b64, sig: b64} or None."""
    rows = get_user_keys(db, user_id)
    if not rows:
        return None
    out = {}
    if "kem" in rows:
        out["kem"] = rows["kem"].public_key
    if "sig" in rows:
        out["sig"] = rows["sig"].public_key
    return out if out else None


def get_user_private_key(db: Session, user_id: int, key_type: str) -> str | None:
    """Get private key for user (kem or sig). Returns base64 string or None.
    Decrypts if stored in v2 encrypted form.
    """
    row = db.query(KeyPair).filter(
        KeyPair.user_id == user_id,
        KeyPair.key_type == key_type,
    ).first()
    if not row:
        return None
    try:
        return _decrypt_private_key(row.private_key)
    except ValueError:
        raise
