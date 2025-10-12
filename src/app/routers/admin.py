"""Simple admin panel for managing users and viewing interactions."""

from __future__ import annotations

import asyncio
import secrets
import time
from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.database import get_db_session
from app.models.db.user import User
from app.models.db.repositories import list_recent_conversations
from app.services.passwords import hash_password, verify_password
from app.services.auth_2fa import two_factor_service

try:  # optional redis for admin sessions
    from redis.asyncio import Redis as _Redis
except Exception:  # pragma: no cover
    _Redis = None  # type: ignore

router = APIRouter(prefix="/admin", tags=["admin"], include_in_schema=False)
templates = Jinja2Templates(directory="src/app/web/templates")

ADMIN_COOKIE = "sparkone_admin_session"
SESSION_TTL = 8 * 3600
ADMIN_CSRF_COOKIE = "sparkone_admin_csrftoken"

_admin_sessions: dict[str, float] = {}
_lock = asyncio.Lock()
_redis_client: _Redis | None = None


def _get_redis(settings: Settings) -> _Redis | None:
    global _redis_client
    if _Redis is None:
        return None
    if _redis_client is None and settings.redis_url:
        _redis_client = _Redis.from_url(settings.redis_url)
    return _redis_client


def _generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def _set_admin_csrf_cookie(response: Response, token: str, settings: Settings) -> None:
    secure = settings.environment == "production"
    response.set_cookie(
        ADMIN_CSRF_COOKIE,
        token,
        max_age=3600,
        httponly=False,
        samesite="lax",
        secure=secure,
    )


def _validate_admin_csrf(request: Request, form_data: dict[str, Any]) -> bool:
    cookie_token = request.cookies.get(ADMIN_CSRF_COOKIE)
    form_token = form_data.get("csrf_token")
    header_token = request.headers.get("X-CSRFToken")
    candidate = form_token or header_token
    return bool(cookie_token and candidate and cookie_token == candidate)


async def _session_add(token: str, settings: Settings) -> None:
    r = _get_redis(settings)
    if r is not None:
        await r.setex(f"sparkone:admin_session:{token}", SESSION_TTL, "1")
        return
    async with _lock:
        _admin_sessions[token] = time.time() + SESSION_TTL


async def _session_check(token: str, settings: Settings) -> bool:
    r = _get_redis(settings)
    if r is not None:
        ttl = await r.ttl(f"sparkone:admin_session:{token}")
        if ttl is None or ttl < 0:
            return False
        await r.expire(f"sparkone:admin_session:{token}", SESSION_TTL)
        return True
    async with _lock:
        exp = _admin_sessions.get(token)
        if not exp:
            return False
        if exp <= time.time():
            _admin_sessions.pop(token, None)
            return False
        _admin_sessions[token] = time.time() + SESSION_TTL
        return True


async def _require_admin(request: Request, session: AsyncSession, settings: Settings) -> User:
    token = request.cookies.get(ADMIN_COOKIE)
    if not token or not await _session_check(token, settings):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin login required")
    # Optionally we could map token->user; for MVP treat as authenticated admin
    # and show content gated by admin flag when actions occur.
    # Here we pick the latest admin user for context only.
    result = await session.execute(select(User).where(User.is_admin == True).limit(1))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No admin configured")
    return user


@router.get("/login", response_class=HTMLResponse)
async def admin_login_form(request: Request) -> HTMLResponse:
    """Exibe formulário de login admin com CSRF token."""
    csrf = _generate_csrf_token()
    response = templates.TemplateResponse(
        "admin_login.html", {"request": request, "error": None, "csrf_token": csrf}
    )
    _set_admin_csrf_cookie(response, csrf, get_settings())
    return response


@router.post("/login")
async def admin_login(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    totp: str | None = Form(None),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
):
    # CSRF validation for login form
    form = await request.form()
    if not _validate_admin_csrf(request, dict(form)):
        return templates.TemplateResponse(
            "admin_login.html",
            {"request": request, "error": "Token de segurança inválido", "csrf_token": _generate_csrf_token()},
            status_code=400,
        )
    result = await session.execute(select(User).where(User.email == email))
    user: User | None = result.scalar_one_or_none()
    if not user or not user.is_active or not user.is_admin:
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Acesso negado"}, status_code=401)
    if not verify_password(password, user.password_hash):
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Credenciais inválidas"}, status_code=401)
    # 2FA if enabled
    if user.two_factor_enabled:
        if not totp:
            return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Informe o token 2FA"}, status_code=401)
        ok = await two_factor_service.verify_2fa_login(user.id, totp, session)
        if not ok:
            return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Token 2FA inválido"}, status_code=401)

    token = secrets.token_urlsafe(32)
    await _session_add(token, settings)
    secure = settings.environment == "production"
    resp = RedirectResponse(url="/admin", status_code=302)
    resp.set_cookie(ADMIN_COOKIE, token, max_age=SESSION_TTL, httponly=True, samesite="lax", secure=secure)
    # Provision new CSRF token after login
    _set_admin_csrf_cookie(resp, _generate_csrf_token(), settings)
    return resp


@router.get("/logout")
async def admin_logout() -> RedirectResponse:
    resp = RedirectResponse(url="/admin/login", status_code=302)
    resp.delete_cookie(ADMIN_COOKIE)
    return resp


@router.get("/", response_class=HTMLResponse)
async def admin_index(request: Request, session: AsyncSession = Depends(get_db_session), settings: Settings = Depends(get_settings)) -> HTMLResponse:
    await _require_admin(request, session, settings)
    csrf = _generate_csrf_token()
    response = templates.TemplateResponse("admin_dashboard.html", {"request": request, "csrf_token": csrf})
    _set_admin_csrf_cookie(response, csrf, settings)
    return response


@router.get("/users", response_class=HTMLResponse)
async def admin_users(request: Request, session: AsyncSession = Depends(get_db_session), settings: Settings = Depends(get_settings)) -> HTMLResponse:
    await _require_admin(request, session, settings)
    result = await session.execute(select(User).order_by(User.id.desc()))
    users = result.scalars().all()
    csrf = _generate_csrf_token()
    response = templates.TemplateResponse(
        "admin_users.html", {"request": request, "users": users, "csrf_token": csrf}
    )
    _set_admin_csrf_cookie(response, csrf, settings)
    return response


@router.post("/users", response_class=HTMLResponse)
async def admin_create_user(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    email: str = Form(...),
    password: str = Form(...),
    is_admin: bool = Form(False),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    await _require_admin(request, session, settings)
    form = await request.form()
    if not _validate_admin_csrf(request, dict(form)):
        return templates.TemplateResponse(
            "admin_users.html", {"request": request, "error": "Token de segurança inválido", "users": []}, status_code=400
        )
    exists = await session.execute(select(User).where(User.email == email))
    if exists.scalar_one_or_none():
        return templates.TemplateResponse("admin_users.html", {"request": request, "error": "Usuário já existe"}, status_code=400)
    user = User(email=email, password_hash=hash_password(password), is_active=True, is_verified=True, is_admin=is_admin)
    session.add(user)
    await session.commit()
    result = await session.execute(select(User).order_by(User.id.desc()))
    users = result.scalars().all()
    csrf = _generate_csrf_token()
    response = templates.TemplateResponse(
        "admin_users.html", {"request": request, "users": users, "message": "Usuário criado", "csrf_token": csrf}
    )
    _set_admin_csrf_cookie(response, csrf, settings)
    return response


@router.post("/users/{user_id}/password", response_class=HTMLResponse)
async def admin_set_user_password(
    request: Request,
    user_id: int,
    new_password: str = Form(...),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    await _require_admin(request, session, settings)
    form = await request.form()
    if not _validate_admin_csrf(request, dict(form)):
        return templates.TemplateResponse(
            "admin_users.html", {"request": request, "error": "Token de segurança inválido", "users": []}, status_code=400
        )
    result = await session.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u:
        return templates.TemplateResponse(
            "admin_users.html", {"request": request, "error": "Usuário não encontrado", "users": []}, status_code=404
        )
    if not new_password or len(new_password) < 8:
        result = await session.execute(select(User).order_by(User.id.desc()))
        users = result.scalars().all()
        return templates.TemplateResponse(
            "admin_users.html", {"request": request, "users": users, "error": "Senha deve ter ao menos 8 caracteres"}, status_code=400
        )
    u.password_hash = hash_password(new_password)
    await session.commit()
    result = await session.execute(select(User).order_by(User.id.desc()))
    users = result.scalars().all()
    csrf = _generate_csrf_token()
    response = templates.TemplateResponse(
        "admin_users.html", {"request": request, "users": users, "message": "Senha atualizada", "csrf_token": csrf}
    )
    _set_admin_csrf_cookie(response, csrf, settings)
    return response


@router.post("/users/{user_id}/toggle-active", response_class=HTMLResponse)
async def admin_toggle_active(
    request: Request,
    user_id: int,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    await _require_admin(request, session, settings)
    form = await request.form()
    if not _validate_admin_csrf(request, dict(form)):
        return templates.TemplateResponse(
            "admin_users.html", {"request": request, "error": "Token de segurança inválido", "users": []}, status_code=400
        )
    result = await session.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u:
        return templates.TemplateResponse(
            "admin_users.html", {"request": request, "error": "Usuário não encontrado", "users": []}, status_code=404
        )
    u.is_active = not bool(u.is_active)
    await session.commit()
    result = await session.execute(select(User).order_by(User.id.desc()))
    users = result.scalars().all()
    csrf = _generate_csrf_token()
    response = templates.TemplateResponse(
        "admin_users.html", {"request": request, "users": users, "message": "Status alterado", "csrf_token": csrf}
    )
    _set_admin_csrf_cookie(response, csrf, settings)
    return response


@router.post("/users/{user_id}/toggle-admin", response_class=HTMLResponse)
async def admin_toggle_admin(
    request: Request,
    user_id: int,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    await _require_admin(request, session, settings)
    form = await request.form()
    if not _validate_admin_csrf(request, dict(form)):
        return templates.TemplateResponse(
            "admin_users.html", {"request": request, "error": "Token de segurança inválido", "users": []}, status_code=400
        )
    result = await session.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u:
        return templates.TemplateResponse(
            "admin_users.html", {"request": request, "error": "Usuário não encontrado", "users": []}, status_code=404
        )
    if u.is_admin:
        # Prevent removing the last admin
        admins = (await session.execute(select(User).where(User.is_admin == True))).scalars().all()
        if len(admins) <= 1:
            result = await session.execute(select(User).order_by(User.id.desc()))
            users = result.scalars().all()
            return templates.TemplateResponse(
                "admin_users.html", {"request": request, "users": users, "error": "Não é possível remover o único admin"}, status_code=400
            )
    u.is_admin = not bool(u.is_admin)
    await session.commit()
    result = await session.execute(select(User).order_by(User.id.desc()))
    users = result.scalars().all()
    csrf = _generate_csrf_token()
    response = templates.TemplateResponse(
        "admin_users.html", {"request": request, "users": users, "message": "Permissão atualizada", "csrf_token": csrf}
    )
    _set_admin_csrf_cookie(response, csrf, settings)
    return response


@router.post("/users/{user_id}/reset-2fa", response_class=HTMLResponse)
async def admin_reset_2fa(
    request: Request,
    user_id: int,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    await _require_admin(request, session, settings)
    form = await request.form()
    if not _validate_admin_csrf(request, dict(form)):
        return templates.TemplateResponse(
            "admin_users.html", {"request": request, "error": "Token de segurança inválido", "users": []}, status_code=400
        )
    result = await session.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u:
        return templates.TemplateResponse(
            "admin_users.html", {"request": request, "error": "Usuário não encontrado", "users": []}, status_code=404
        )
    u.two_factor_enabled = False
    u.totp_secret = None
    u.backup_codes = None
    await session.commit()
    result = await session.execute(select(User).order_by(User.id.desc()))
    users = result.scalars().all()
    csrf = _generate_csrf_token()
    response = templates.TemplateResponse(
        "admin_users.html", {"request": request, "users": users, "message": "2FA redefinido", "csrf_token": csrf}
    )
    _set_admin_csrf_cookie(response, csrf, settings)
    return response


@router.post("/users/{user_id}/delete", response_class=HTMLResponse)
async def admin_delete_user(
    request: Request,
    user_id: int,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    await _require_admin(request, session, settings)
    form = await request.form()
    if not _validate_admin_csrf(request, dict(form)):
        return templates.TemplateResponse(
            "admin_users.html", {"request": request, "error": "Token de segurança inválido", "users": []}, status_code=400
        )
    result = await session.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if not u:
        return templates.TemplateResponse(
            "admin_users.html", {"request": request, "error": "Usuário não encontrado", "users": []}, status_code=404
        )
    if u.is_admin:
        admins = (await session.execute(select(User).where(User.is_admin == True))).scalars().all()
        if len(admins) <= 1:
            result = await session.execute(select(User).order_by(User.id.desc()))
            users = result.scalars().all()
            return templates.TemplateResponse(
                "admin_users.html", {"request": request, "users": users, "error": "Não é possível excluir o único admin"}, status_code=400
            )
    await session.delete(u)
    await session.commit()
    result = await session.execute(select(User).order_by(User.id.desc()))
    users = result.scalars().all()
    csrf = _generate_csrf_token()
    response = templates.TemplateResponse(
        "admin_users.html", {"request": request, "users": users, "message": "Usuário excluído", "csrf_token": csrf}
    )
    _set_admin_csrf_cookie(response, csrf, settings)
    return response


@router.get("/interactions", response_class=HTMLResponse)
async def admin_interactions(request: Request, session: AsyncSession = Depends(get_db_session), settings: Settings = Depends(get_settings)) -> HTMLResponse:
    await _require_admin(request, session, settings)
    conversations = await list_recent_conversations(session, limit=25)
    csrf = _generate_csrf_token()
    response = templates.TemplateResponse(
        "admin_interactions.html", {"request": request, "conversations": conversations, "csrf_token": csrf}
    )
    _set_admin_csrf_cookie(response, csrf, settings)
    return response


# 2FA Setup & Password Change
@router.get("/2fa/setup", response_class=HTMLResponse)
async def admin_2fa_setup(request: Request, session: AsyncSession = Depends(get_db_session), settings: Settings = Depends(get_settings)) -> HTMLResponse:
    user = await _require_admin(request, session, settings)
    data = await two_factor_service.setup_2fa(user.id, session)
    csrf = _generate_csrf_token()
    response = templates.TemplateResponse("admin_2fa_setup.html", {"request": request, **data, "csrf_token": csrf})
    _set_admin_csrf_cookie(response, csrf, settings)
    return response


@router.post("/2fa/verify", response_class=HTMLResponse)
async def admin_2fa_verify(request: Request, token: str = Form(...), session: AsyncSession = Depends(get_db_session), settings: Settings = Depends(get_settings)) -> HTMLResponse:
    user = await _require_admin(request, session, settings)
    form = await request.form()
    if not _validate_admin_csrf(request, dict(form)):
        return templates.TemplateResponse(
            "admin_2fa_setup.html", {"request": request, "error": "Token de segurança inválido"}, status_code=400
        )
    ok = await two_factor_service.verify_2fa_setup(user.id, token, session)
    if not ok:
        return templates.TemplateResponse("admin_2fa_setup.html", {"request": request, "error": "Token inválido"}, status_code=400)
    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "message": "2FA habilitado"})


@router.get("/password", response_class=HTMLResponse)
async def admin_password_form(request: Request, session: AsyncSession = Depends(get_db_session), settings: Settings = Depends(get_settings)) -> HTMLResponse:
    await _require_admin(request, session, settings)
    csrf = _generate_csrf_token()
    response = templates.TemplateResponse("admin_password.html", {"request": request, "csrf_token": csrf})
    _set_admin_csrf_cookie(response, csrf, settings)
    return response


@router.post("/password", response_class=HTMLResponse)
async def admin_password_change(
    request: Request,
    current: str = Form(...),
    new: str = Form(...),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    user = await _require_admin(request, session, settings)
    form = await request.form()
    if not _validate_admin_csrf(request, dict(form)):
        return templates.TemplateResponse("admin_password.html", {"request": request, "error": "Token de segurança inválido"}, status_code=400)
    if not verify_password(current, user.password_hash):
        return templates.TemplateResponse("admin_password.html", {"request": request, "error": "Senha atual incorreta"}, status_code=400)
    user.password_hash = hash_password(new)
    await session.commit()
    csrf = _generate_csrf_token()
    response = templates.TemplateResponse("admin_dashboard.html", {"request": request, "message": "Senha alterada", "csrf_token": csrf})
    _set_admin_csrf_cookie(response, csrf, settings)
    return response


__all__ = ["router"]
