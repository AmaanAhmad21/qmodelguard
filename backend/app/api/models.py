"""Model file endpoints."""
import base64
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services import qcrypto, storage

router = APIRouter()


@router.post("/upload")
async def upload_model(
    file: UploadFile = File(...),
    # TODO: Add auth dependency (user_id from token)
    db: Session = Depends(get_db),
):
    """Upload a model file.
    TODO: Associate with authenticated user in DB.
    """
    content = await file.read()
    user_id = 1  # TODO: from auth
    storage_path = storage.save_file(content, file.filename or "model", user_id)
    return {"id": "mock_model_1", "filename": file.filename, "storage_path": storage_path}


@router.get("/{id}")
async def get_model(
    id: str,
    db: Session = Depends(get_db),
):
    """Download a model file by id.
    TODO: Lookup in DB, verify user access.
    """
    # TODO: Lookup model in DB by id, get storage_path
    if id == "notfound":
        raise HTTPException(status_code=404, detail="Model not found")
    # Mock: return empty bytes for now (no real file lookup)
    return Response(content=b"mock_model_content", media_type="application/octet-stream")


@router.post("/encrypt")
async def encrypt_model(
    model: UploadFile = File(...),
    recipient_id: str = Form(...),
    db: Session = Depends(get_db),
):
    """Encrypt model for recipient.
    TODO: Get recipient public key, use qcrypto.encrypt.
    """
    content = await model.read()
    # Stub: qcrypto.encrypt would be called here
    return {"encrypted_model_id": "mock_enc_1", "recipient_id": recipient_id}


@router.post("/decrypt")
async def decrypt_model(
    model: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Decrypt model with your private key.
    TODO: Use qcrypto.decrypt with user's private key.
    """
    content = await model.read()
    return {"decrypted_model_id": "mock_dec_1"}


@router.post("/sign")
async def sign_model(
    model: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Sign model with your signature key.
    TODO: Use qcrypto.sign with user's sig private key.
    """
    content = await model.read()
    sig_b64 = base64.b64encode(b"mock_signature").decode()
    return {"signature": sig_b64}


@router.post("/verify")
async def verify_model(
    model: UploadFile = File(...),
    signature: UploadFile = File(...),
    signer_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Verify signature on model.
    TODO: Get signer public key, use qcrypto.verify.
    """
    content = await model.read()
    sig_content = await signature.read()
    return {"valid": True}

