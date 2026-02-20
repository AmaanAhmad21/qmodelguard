"""Key storage: persist and retrieve keypairs from DB."""
from sqlalchemy.orm import Session

from app.db.models import KeyPair
from app.services import qcrypto


def store_keypairs_for_user(db: Session, user_id: int) -> None:
    """Generate and store KEM + Sig keypairs for a new user."""
    kem = qcrypto.generate_kem_keypair()
    sig = qcrypto.generate_sig_keypair()
    pub_kem, priv_kem = qcrypto.keys_to_base64(kem)
    pub_sig, priv_sig = qcrypto.keys_to_base64(sig)
    _upsert(db, user_id, "kem", pub_kem, priv_kem)
    _upsert(db, user_id, "sig", pub_sig, priv_sig)


def _upsert(db: Session, user_id: int, key_type: str, pub_b64: str, priv_b64: str) -> int:
    existing = db.query(KeyPair).filter(
        KeyPair.user_id == user_id,
        KeyPair.key_type == key_type,
    ).first()
    if existing:
        existing.public_key = pub_b64
        existing.private_key = priv_b64
        db.commit()
        return existing.id
    kp = KeyPair(
        user_id=user_id,
        key_type=key_type,
        public_key=pub_b64,
        private_key=priv_b64,
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
    """Get private key for user (kem or sig). Returns base64 string or None."""
    row = db.query(KeyPair).filter(
        KeyPair.user_id == user_id,
        KeyPair.key_type == key_type,
    ).first()
    return row.private_key if row else None
