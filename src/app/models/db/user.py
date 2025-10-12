"""Modelo de usuário com suporte a 2FA."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base


class User(Base):
    """Modelo de usuário com autenticação de dois fatores."""

    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # 2FA fields
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    totp_secret = Column(String(32), nullable=True)  # Base32 secret
    backup_codes = Column(Text, nullable=True)  # JSON array of hashed codes

    # Timestamps
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(
    ), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Session management
    session_token = Column(String(255), nullable=True)
    session_expires = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', 2fa_enabled={self.two_factor_enabled})>"

    def to_dict(self) -> dict[str, Any]:
        """Converte o usuário para dicionário."""
        return {
            "id": self.id,
            "email": self.email,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "two_factor_enabled": self.two_factor_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

    def is_session_valid(self) -> bool:
        """Verifica se a sessão do usuário é válida."""
        if not self.session_token or not self.session_expires:
            return False
        return datetime.utcnow() < self.session_expires

    def has_2fa_enabled(self) -> bool:
        """Verifica se o usuário tem 2FA habilitado."""
        return self.two_factor_enabled and self.totp_secret is not None
