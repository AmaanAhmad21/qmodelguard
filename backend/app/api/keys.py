"""Key management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.services import qcrypto

router = APIRouter()


class GenerateKeysResponse(BaseModel):
    """Response for key generation."""
    kem_key_id: str
    sig_key_id: str


@router.post("/generate", response_model=GenerateKeysResponse)
def generate_keys(
    # TODO: Add auth dependency (current_user)
    db: Session = Depends(get_db),
):
    """Generate new Kyber KEM + Dilithium signature keypairs.
    TODO: Associate with authenticated user.
    """
    kem = qcrypto.generate_kem_keypair()
    sig = qcrypto.generate_sig_keypair()

    # TODO: Store in DB for current user
    return GenerateKeysResponse(
        kem_key_id="mock_kem_1",
        sig_key_id="mock_sig_1",
    )


@router.get("/public")
def get_public_keys(
    # TODO: Add auth dependency
    db: Session = Depends(get_db),
):
    """Get your public keys.
    TODO: Return from DB for current user.
    """
    return {
        "kem_public_key": "mock_kyber_public_key_base64",
        "sig_public_key": "mock_dilithium_public_key_base64",
    }


@router.get("/public/{id}")
def get_public_key_by_id(
    id: str,
    db: Session = Depends(get_db),
):
    """Get another user's public key by user id."""
    # TODO: Lookup user by id, return their public key
    if id == "unknown":
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": id,
        "kem_public_key": "mock_kyber_public_key_base64",
        "sig_public_key": "mock_dilithium_public_key_base64",
    }
