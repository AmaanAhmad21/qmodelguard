"""SQLite models for QModelGuard."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """User account."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KeyPair(Base):
    """Stored Kyber or Dilithium keypair for a user."""
    __tablename__ = "keypairs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_type = Column(String(8), nullable=False)  # "kem" or "sig"
    public_key = Column(Text, nullable=False)  # Base64
    private_key = Column(Text, nullable=False)  # Base64 (TODO: encrypt at rest)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ModelFile(Base):
    """Stored model file metadata."""
    __tablename__ = "models"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(256), nullable=False)
    storage_path = Column(String(512), nullable=False)  # Path on filesystem
    is_encrypted = Column(Integer, default=0)  # 0=plain, 1=encrypted
    signature_b64 = Column(Text, nullable=True)
    signer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    signer = relationship("User", foreign_keys=[signer_id], lazy="joined")


class ActivityLog(Base):
    """Audit trail for user actions."""
    __tablename__ = "activity_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(32), nullable=False)
    detail = Column(String(512), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", lazy="joined")
