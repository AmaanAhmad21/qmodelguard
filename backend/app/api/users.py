"""User auth endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db

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
    """Auth response with token placeholder."""
    token: str
    user_id: str


@router.post("/register", response_model=AuthResponse)
def register(
    body: RegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a new user.
    TODO: Hash password, create user, generate keys, return JWT.
    """
    # TODO: Check username exists
    # TODO: Hash password (e.g. bcrypt)
    # TODO: Create user in DB
    # TODO: Generate keypair for user
    return AuthResponse(token="mock_jwt_token", user_id="1")


@router.post("/login", response_model=AuthResponse)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
):
    """Login with username and password.
    TODO: Verify password, return JWT.
    """
    # TODO: Lookup user, verify password
    if body.username == "bad":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return AuthResponse(token="mock_jwt_token", user_id="1")
