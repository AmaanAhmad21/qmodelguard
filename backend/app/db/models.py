"""SQLite models for QModelGuard."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
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
    """Stored Kyber/Dilithium keypair for a user."""
    __tablename__ = "keypairs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    public_key = Column(Text, nullable=False)  # Base64 or PEM
    private_key = Column(Text, nullable=False)  # Encrypted at rest (TODO)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ModelFile(Base):
    """Stored model file metadata."""
    __tablename__ = "models"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(256), nullable=False)
    storage_path = Column(String(512), nullable=False)  # Path on filesystem
    is_encrypted = Column(Integer, default=0)  # 0=plain, 1=encrypted
    created_at = Column(DateTime(timezone=True), server_default=func.now())
