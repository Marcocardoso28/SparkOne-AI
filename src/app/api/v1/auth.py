"""Rotas de autenticação com 2FA."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.database import get_db_session
from app.infrastructure.database.models.user import User
from app.domain.services.auth_2fa import two_factor_service

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db_session)
) -> User:
    """Dependency para obter o usuário atual."""
    # Try to get session token from cookie or header
    session_token = request.cookies.get("sparkone_session")

    if not session_token:
        # Try Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header[7:]

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de sessão não fornecido"
        )

    # Find user by session token
    result = await session.execute(
        select(User).where(
            User.session_token == session_token,
            User.is_active == True
        )
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_session_valid():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada"
        )

    return user


class LoginRequest(BaseModel):
    """Request de login."""
    username: str | None = None
    email: EmailStr | None = None
    password: str
    totp_token: str | None = None


class LoginResponse(BaseModel):
    """Response de login."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    requires_2fa: bool = False
    user: dict[str, Any]


class TwoFactorSetupResponse(BaseModel):
    """Response da configuração de 2FA."""
    qr_code: str
    manual_entry_key: str
    backup_codes: list[str]


class TwoFactorVerifyRequest(BaseModel):
    """Request de verificação de 2FA."""
    token: str


class PasswordChangeRequest(BaseModel):
    """Request de mudança de senha."""
    current_password: str
    new_password: str


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db_session)
):
    """Login com suporte a 2FA."""
    # Validate that either username or email is provided
    if not request.username and not request.email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username ou email é obrigatório"
        )

    # Find user by username or email
    if request.username:
        result = await session.execute(select(User).where(User.username == request.username))
    else:
        result = await session.execute(select(User).where(User.email == request.email))

    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )

    # Verify password (simple verification for testing)
    if user.password_hash != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )

    # Check if 2FA is required
    if user.two_factor_enabled:
        if not request.totp_token:
            # Preparar dados do usuário antes de qualquer operação
            user_data = user.to_dict()
            return LoginResponse(
                access_token="",
                expires_in=0,
                requires_2fa=True,
                user=user_data
            )

        # Verify 2FA token
        if not await two_factor_service.verify_2fa_login(user.id, request.totp_token, session):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token 2FA inválido"
            )

    # Generate session token
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(hours=24)

    user.session_token = session_token
    user.session_expires = expires_at
    user.last_login = datetime.now(UTC)

    # Preparar dados do usuário antes do commit
    user_data = user.to_dict()
    
    await session.commit()

    # Set session cookie
    response.set_cookie(
        key="sparkone_session",
        value=session_token,
        expires=expires_at,
        httponly=True,
        secure=True,
        samesite="strict"
    )

    return LoginResponse(
        access_token=session_token,
        expires_in=86400,  # 24 hours
        user=user_data
    )


@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """Logout do usuário."""
    # Clear session cookie
    response.delete_cookie(key="sparkone_session")

    return {"message": "Logout realizado com sucesso"}


@router.post("/setup-2fa", response_model=TwoFactorSetupResponse)
async def setup_2fa(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Configura 2FA para o usuário."""
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA já está habilitado para este usuário"
        )

    setup_data = await two_factor_service.setup_2fa(current_user.id, session)

    return TwoFactorSetupResponse(
        qr_code=setup_data["qr_code"],
        manual_entry_key=setup_data["manual_entry_key"],
        backup_codes=setup_data["backup_codes"]
    )


@router.post("/verify-2fa")
async def verify_2fa_setup(
    request: TwoFactorVerifyRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Verifica a configuração de 2FA."""
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA já está habilitado para este usuário"
        )

    if await two_factor_service.verify_2fa_setup(current_user.id, request.token, session):
        return {"message": "2FA configurado com sucesso"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido"
        )


@router.post("/disable-2fa")
async def disable_2fa(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Desabilita 2FA para o usuário."""
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA não está habilitado para este usuário"
        )

    # Verify current password (implement proper verification)

    if await two_factor_service.disable_2fa(current_user.id, request.current_password, session):
        return {"message": "2FA desabilitado com sucesso"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Retorna informações do usuário atual."""
    # Usar to_dict() de forma segura
    try:
        return current_user.to_dict()
    except Exception:
        # Fallback em caso de erro com sessão
        return {
            "id": current_user.id,
            "username": getattr(current_user, 'username', None),
            "email": getattr(current_user, 'email', None),
            "is_active": getattr(current_user, 'is_active', True),
            "is_verified": getattr(current_user, 'is_verified', False),
            "two_factor_enabled": getattr(current_user, 'two_factor_enabled', False),
            "created_at": None,
            "updated_at": None,
            "last_login": None,
        }


__all__ = ["router", "get_current_user"]
