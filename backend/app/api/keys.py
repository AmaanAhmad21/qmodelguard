"""Key management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.services import key_store, qcrypto

router = APIRouter()


class GenerateKeysResponse(BaseModel):
    """Response for key generation."""
    kem_key_id: str
    sig_key_id: str


def _upsert_keypair(db: Session, user_id: int, key_type: str, pub_b64: str, priv_b64: str) -> int:
    from app.services.key_store import _upsert
    return _upsert(db, user_id, key_type, pub_b64, priv_b64)


@router.post("/generate", response_model=GenerateKeysResponse)
def generate_keys(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate new Kyber KEM + Dilithium signature keypairs, store for current user."""
    kem = qcrypto.generate_kem_keypair()
    sig = qcrypto.generate_sig_keypair()
    pub_kem, priv_kem = qcrypto.keys_to_base64(kem)
    pub_sig, priv_sig = qcrypto.keys_to_base64(sig)
    kem_id = _upsert_keypair(db, user.id, "kem", pub_kem, priv_kem)
    sig_id = _upsert_keypair(db, user.id, "sig", pub_sig, priv_sig)
    return GenerateKeysResponse(
        kem_key_id=str(kem_id),
        sig_key_id=str(sig_id),
    )


@router.get("/public")
def get_public_keys(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get your public keys. Returns 404 if no keys generated yet."""
    keys = key_store.get_user_public_keys(db, user.id)
    if not keys or "kem" not in keys or "sig" not in keys:
        raise HTTPException(
            status_code=404,
            detail="No keys found. Call POST /api/keys/generate first.",
        )
    return {
        "kem_public_key": keys["kem"],
        "sig_public_key": keys["sig"],
    }


@router.get("/public/{user_id}")
def get_public_key_by_id(
    user_id: str,
    db: Session = Depends(get_db),
):
    """Get another user's public keys by user id (numeric) or username."""
    try:
        uid = int(user_id)
        target = db.query(User).filter(User.id == uid).first()
    except ValueError:
        target = db.query(User).filter(User.username == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    keys = key_store.get_user_public_keys(db, target.id)
    if not keys or "kem" not in keys or "sig" not in keys:
        raise HTTPException(status_code=404, detail="User has no keys")
    return {
        "user_id": str(target.id),
        "username": target.username,
        "kem_public_key": keys["kem"],
        "sig_public_key": keys["sig"],
    }
