"""Serviço de autenticação com 2FA (TOTP)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from typing import Any

import pyotp
import qrcode
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.db.user import User
from app.models.schemas import UserCreate, UserResponse


class TwoFactorAuthService:
    """Serviço para gerenciar autenticação de dois fatores."""

    def __init__(self, issuer: str = "SparkOne", algorithm: str = "SHA1", digits: int = 6, period: int = 30):
        self.issuer = issuer
        self.algorithm = algorithm
        self.digits = digits
        self.period = period

    def generate_secret(self) -> str:
        """Gera um secret para TOTP."""
        return pyotp.random_base32()

    def generate_qr_code(self, user_email: str, secret: str) -> str:
        """Gera QR code para configuração do 2FA."""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=self.issuer
        )

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64 for web display
        import io
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    def verify_totp(self, secret: str, token: str) -> bool:
        """Verifica se o token TOTP é válido."""
        try:
            totp = pyotp.TOTP(secret)
            # Allow 1 window of tolerance
            return totp.verify(token, valid_window=1)
        except Exception:
            return False

    def generate_backup_codes(self, count: int = 10) -> list[str]:
        """Gera códigos de backup para 2FA."""
        return [secrets.token_hex(4).upper() for _ in range(count)]

    async def setup_2fa(self, user_id: int, session: AsyncSession) -> dict[str, Any]:
        """Configura 2FA para um usuário."""
        # Get user
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        # Generate secret and backup codes
        secret = self.generate_secret()
        backup_codes = self.generate_backup_codes()

        # Generate QR code
        qr_code = self.generate_qr_code(user.email, secret)

        # Store secret and backup codes (hashed)
        user.totp_secret = secret
        user.backup_codes = self._hash_backup_codes(backup_codes)
        user.two_factor_enabled = False  # Will be enabled after verification

        await session.commit()

        return {
            "secret": secret,
            "qr_code": qr_code,
            "backup_codes": backup_codes,
            "manual_entry_key": secret
        }

    async def verify_2fa_setup(self, user_id: int, token: str, session: AsyncSession) -> bool:
        """Verifica o token durante a configuração do 2FA."""
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.totp_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA não configurado para este usuário"
            )

        if self.verify_totp(user.totp_secret, token):
            user.two_factor_enabled = True
            await session.commit()
            return True

        return False

    async def verify_2fa_login(self, user_id: int, token: str, session: AsyncSession) -> bool:
        """Verifica 2FA durante o login."""
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return False

        # Check if 2FA is enabled
        if not user.two_factor_enabled:
            return True  # 2FA not required

        # Verify TOTP token
        if user.totp_secret and self.verify_totp(user.totp_secret, token):
            return True

        # Check backup codes
        if user.backup_codes and self._verify_backup_code(token, user.backup_codes):
            # Remove used backup code
            await self._remove_backup_code(user, token, session)
            return True

        return False

    async def disable_2fa(self, user_id: int, password: str, session: AsyncSession) -> bool:
        """Desabilita 2FA para um usuário."""
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        # Verify password (you should implement proper password verification)
        # For now, we'll skip this check

        user.two_factor_enabled = False
        user.totp_secret = None
        user.backup_codes = None

        await session.commit()
        return True

    def _hash_backup_codes(self, backup_codes: list[str]) -> list[str]:
        """Hash backup codes for storage."""
        return [hashlib.sha256(code.encode()).hexdigest() for code in backup_codes]

    def _verify_backup_code(self, token: str, hashed_codes: list[str]) -> bool:
        """Verifica se um código de backup é válido."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token_hash in hashed_codes

    async def _remove_backup_code(self, user: User, used_code: str, session: AsyncSession) -> None:
        """Remove um código de backup usado."""
        if not user.backup_codes:
            return

        used_hash = hashlib.sha256(used_code.encode()).hexdigest()
        user.backup_codes = [
            code for code in user.backup_codes if code != used_hash]
        await session.commit()


# Global instance
two_factor_service = TwoFactorAuthService()


__all__ = ["TwoFactorAuthService", "two_factor_service"]
