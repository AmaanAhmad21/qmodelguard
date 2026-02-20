"""User auth endpoints."""
import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user
from app.db.database import get_db
from app.db.models import User
from app.services import key_store

router = APIRouter()


class RegisterRequest(BaseModel):
    """Registration payload."""
    username: str
    password: str


class LoginRequest(BaseModel):
    """Login payload."""
    username: str
    password: str


class AuthResponse(BaseModel):
    """Auth response with JWT."""
    token: str
    user_id: str


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


@router.post("/register", response_model=AuthResponse)
def register(
    body: RegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a new user. Hashes password, creates user in DB, returns JWT."""
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    password_hash = _hash_password(body.password)
    user = User(username=body.username, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    key_store.store_keypairs_for_user(db, user.id)
    token = create_access_token({"sub": str(user.id)})
    return AuthResponse(token=token, user_id=str(user.id))


@router.post("/login", response_model=AuthResponse)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
):
    """Login with username and password. Returns JWT."""
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not _verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return AuthResponse(token=token, user_id=str(user.id))


@router.get("/me")
def me(
    user: User = Depends(get_current_user),
):
    """Get current user (requires auth)."""
    return {"user_id": str(user.id), "username": user.username}
