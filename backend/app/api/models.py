"""Model file endpoints."""
import base64
import os
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.api.activity import log_activity
from app.db.database import get_db
from app.db.models import ModelFile, User
from app.limiter import limiter
from app.services import key_store, qcrypto, storage

router = APIRouter()

_UPLOAD_LIMIT = os.getenv("RATE_LIMIT_UPLOAD", "20/minute")
ALLOWED_EXTENSIONS = {".pt", ".safetensors", ".onnx", ".h5"}
MAX_MODEL_SIZE_MB = float(os.getenv("MAX_MODEL_SIZE_MB", "512"))  # 512 MB default
MAX_MODEL_SIZE_BYTES = int(MAX_MODEL_SIZE_MB * 1024 * 1024)

class EncryptRequest(BaseModel):
    model_id: int
    recipient_id: str
    sign: bool = True

class DecryptRequest(BaseModel):
    model_id: int

class SignRequest(BaseModel):
    model_id: int

class VerifyRequest(BaseModel):
    model_id: int


def _get_user_by_id_or_username(db: Session, user_id_or_username: str) -> Optional[User]:
    try:
        uid = int(user_id_or_username)
        return db.query(User).filter(User.id == uid).first()
    except ValueError:
        return db.query(User).filter(User.username == user_id_or_username).first()


def _get_model_owned(db: Session, model_id: int, user_id: int) -> ModelFile:
    model = db.query(ModelFile).filter(ModelFile.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if model.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return model


def _sign_model_data(db: Session, user_id: int, data: bytes) -> str:
    """Sign raw bytes with user's Dilithium key. Returns base64 signature."""
    priv_b64 = key_store.get_user_private_key(db, user_id, "sig")
    if not priv_b64:
        raise HTTPException(status_code=404, detail="No signature private key found")
    sig_bytes = qcrypto.sign_data(base64.b64decode(priv_b64), data)
    return base64.b64encode(sig_bytes).decode("ascii")


@router.post("/upload")
@limiter.limit(_UPLOAD_LIMIT)
async def upload_model(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a model file. Automatically signed by uploader."""
    content = await file.read()
    if len(content) > MAX_MODEL_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Model file too large")

    filename = file.filename or "model"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model extension '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )
    storage_path = storage.save_file(content, filename, user.id)
    sig_b64 = _sign_model_data(db, user.id, content)

    model = ModelFile(
        user_id=user.id,
        filename=filename,
        storage_path=storage_path,
        is_encrypted=0,
        signature_b64=sig_b64,
        signer_id=user.id,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    log_activity(db, user.id, "upload", f"Uploaded and signed {filename}")
    return {"id": str(model.id), "filename": model.filename}


@router.get("")
async def list_models(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """List current user's models."""
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be >= 0")
    q = db.query(ModelFile).filter(ModelFile.user_id == user.id).order_by(ModelFile.id.desc())
    total = q.count()
    rows = q.offset(offset).limit(limit).all()
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": str(m.id),
                "filename": m.filename,
                "is_encrypted": bool(m.is_encrypted),
                "is_signed": bool(m.signature_b64),
                "signer": m.signer.username if m.signer else None,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in rows
        ],
    }


@router.get("/{id}")
async def get_model(
    id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download a model file by id."""
    try:
        mid = int(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid model id")

    model = _get_model_owned(db, mid, user.id)

    full_path = storage.BACKEND_ROOT / model.storage_path
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File missing on disk")

    return FileResponse(
        path=str(full_path),
        media_type="application/octet-stream",
        filename=model.filename,
    )


@router.delete("/{id}")
async def delete_model(
    id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a model you own."""
    try:
        mid = int(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid model id")

    model = _get_model_owned(db, mid, user.id)

    model_name = model.filename
    try:
        storage.delete_file(model.storage_path)
    except Exception:
        pass
    db.delete(model)
    db.commit()
    log_activity(db, user.id, "delete", f"Deleted {model_name}")
    return {"deleted": str(mid)}


@router.post("/encrypt")
async def encrypt_model(
    body: EncryptRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Encrypt and sign a model for a recipient.

    The encrypted copy is stored under the recipient's account with the
    sender's signature attached so they can verify authenticity.
    """
    model = _get_model_owned(db, body.model_id, user.id)

    recipient = _get_user_by_id_or_username(db, body.recipient_id)
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    recipient_pub = key_store.get_user_public_keys(db, recipient.id)
    if not recipient_pub or "kem" not in recipient_pub:
        raise HTTPException(status_code=404, detail="Recipient has no KEM public key")

    plaintext = storage.load_file(model.storage_path)

    sig_b64 = None
    signer_id = None
    if body.sign:
        sig_b64 = _sign_model_data(db, user.id, plaintext)
        signer_id = user.id

    pub_bytes = base64.b64decode(recipient_pub["kem"])
    ciphertext = qcrypto.encrypt_data(pub_bytes, plaintext)

    enc_filename = f"{model.filename}.enc"
    enc_path = storage.save_file(ciphertext, enc_filename, recipient.id)

    enc_model = ModelFile(
        user_id=recipient.id,
        filename=enc_filename,
        storage_path=enc_path,
        is_encrypted=1,
        signature_b64=sig_b64,
        signer_id=signer_id,
    )
    db.add(enc_model)
    db.commit()
    db.refresh(enc_model)
    action_desc = f"Encrypted{' & signed' if body.sign else ''} {model.filename} for {recipient.username}"
    log_activity(db, user.id, "encrypt", action_desc)

    return {
        "encrypted_model_id": str(enc_model.id),
        "recipient_user_id": str(recipient.id),
    }


@router.post("/decrypt")
async def decrypt_model(
    body: DecryptRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Decrypt an encrypted model you own."""
    enc_model = _get_model_owned(db, body.model_id, user.id)
    if not enc_model.is_encrypted:
        raise HTTPException(status_code=400, detail="Model is not marked as encrypted")

    priv_b64 = key_store.get_user_private_key(db, user.id, "kem")
    if not priv_b64:
        raise HTTPException(status_code=404, detail="No KEM private key found")

    ciphertext = storage.load_file(enc_model.storage_path)
    priv_bytes = base64.b64decode(priv_b64)
    plaintext = qcrypto.decrypt_data(priv_bytes, ciphertext)

    out_filename = enc_model.filename.removesuffix(".enc")
    out_path = storage.save_file(plaintext, out_filename, user.id)

    dec_model = ModelFile(
        user_id=user.id,
        filename=out_filename,
        storage_path=out_path,
        is_encrypted=0,
        signature_b64=enc_model.signature_b64,
        signer_id=enc_model.signer_id,
    )
    db.add(dec_model)
    db.commit()
    db.refresh(dec_model)
    log_activity(db, user.id, "decrypt", f"Decrypted {enc_model.filename}")
    return {"decrypted_model_id": str(dec_model.id)}


@router.post("/sign")
async def sign_model(
    body: SignRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sign a model you own. Signature is stored on the model record."""
    model = _get_model_owned(db, body.model_id, user.id)
    data = storage.load_file(model.storage_path)
    sig_b64 = _sign_model_data(db, user.id, data)

    model.signature_b64 = sig_b64
    model.signer_id = user.id
    db.commit()

    log_activity(db, user.id, "sign", f"Signed {model.filename}")
    return {"signed": True, "model_id": str(model.id)}


@router.post("/verify")
async def verify_model(
    body: VerifyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify the stored signature on a model. No manual paste needed."""
    model = _get_model_owned(db, body.model_id, user.id)
    if not model.signature_b64 or not model.signer_id:
        raise HTTPException(status_code=400, detail="Model has no signature")

    pub = key_store.get_user_public_keys(db, model.signer_id)
    if not pub or "sig" not in pub:
        raise HTTPException(status_code=404, detail="Signer has no signature public key")

    data = storage.load_file(model.storage_path)
    sig_bytes = base64.b64decode(model.signature_b64)
    pub_bytes = base64.b64decode(pub["sig"])
    valid = bool(qcrypto.verify_signature(pub_bytes, data, sig_bytes))

    signer_name = model.signer.username if model.signer else str(model.signer_id)
    log_activity(db, user.id, "verify", f"Verified {model.filename} by {signer_name} ({'valid' if valid else 'invalid'})")
    return {"valid": valid, "signer": signer_name}
