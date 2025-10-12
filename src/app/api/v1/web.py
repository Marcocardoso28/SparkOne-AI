"""Minimal Web UI for manual interactions (text, voice, images)."""

from __future__ import annotations

import asyncio
import secrets
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

import structlog
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic
from fastapi.templating import Jinja2Templates

from app.config import Settings, get_settings
from app.infrastructure.database.database import get_db_session
from app.api.dependencies import get_ingestion_service
from app.infrastructure.database.models.repositories import list_recent_conversations
from app.models.schemas import Channel, ChannelMessage
from app.domain.services.ingestion import IngestionService

try:  # pragma: no cover - opcional
    from redis.asyncio import Redis
except ImportError:  # pragma: no cover
    Redis = None  # type: ignore[assignment]

router = APIRouter(tags=["web"], include_in_schema=False)
security = HTTPBasic()
templates = Jinja2Templates(directory="src/app/web/templates")
logger = structlog.get_logger(__name__)

CSRF_COOKIE = "sparkone_csrftoken"
CSRF_HEADER = "X-SparkOne-CSRF"
SESSION_COOKIE = "sparkone_session"
LOGIN_SESSION_COOKIE = "sparkone_login_session"

SESSION_TTL_SECONDS = 8 * 3600


class SessionStore(Protocol):
    async def add(self, token: str, ttl: int) -> None: ...

    async def remove(self, token: str) -> None: ...

    async def is_active(self, token: str) -> bool: ...

    async def touch(self, token: str, ttl: int) -> None: ...


class InMemorySessionStore(SessionStore):
    def __init__(self) -> None:
        self._sessions: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def add(self, token: str, ttl: int) -> None:
        async with self._lock:
            self._sessions[token] = time.time() + ttl

    async def remove(self, token: str) -> None:
        async with self._lock:
            self._sessions.pop(token, None)

    async def is_active(self, token: str) -> bool:
        async with self._lock:
            expiry = self._sessions.get(token)
            if not expiry:
                return False
            if expiry <= time.time():
                self._sessions.pop(token, None)
                return False
            return True

    async def touch(self, token: str, ttl: int) -> None:
        async with self._lock:
            if token in self._sessions:
                self._sessions[token] = time.time() + ttl


class RedisSessionStore(SessionStore):
    def __init__(self, redis_url: str, *, prefix: str = "sparkone:web_session:") -> None:
        if Redis is None:  # pragma: no cover
            raise RuntimeError("redis.asyncio não está disponível")
        self._client = Redis.from_url(redis_url)
        self._prefix = prefix

    def _key(self, token: str) -> str:
        return f"{self._prefix}{token}"

    async def add(self, token: str, ttl: int) -> None:
        await self._client.setex(self._key(token), ttl, "1")

    async def remove(self, token: str) -> None:
        await self._client.delete(self._key(token))

    async def is_active(self, token: str) -> bool:
        ttl_left = await self._client.ttl(self._key(token))
        if ttl_left is None or ttl_left < 0:
            return False
        if ttl_left == -1:
            await self._client.expire(self._key(token), SESSION_TTL_SECONDS)
            return True
        return ttl_left > 0

    async def touch(self, token: str, ttl: int) -> None:
        await self._client.expire(self._key(token), ttl)


_in_memory_session_store = InMemorySessionStore()
_redis_session_stores: dict[str, SessionStore] = {}


def _get_session_store(settings: Settings) -> SessionStore:
    if settings.redis_url and Redis is not None:
        store = _redis_session_stores.get(settings.redis_url)
        if store is None:
            store = RedisSessionStore(settings.redis_url)
            _redis_session_stores[settings.redis_url] = store
        return store
    return _in_memory_session_store


async def _add_session(token: str, settings: Settings) -> None:
    await _get_session_store(settings).add(token, settings.web_session_ttl_seconds)


async def _remove_session(token: str, settings: Settings) -> None:
    await _get_session_store(settings).remove(token)


async def _touch_session(token: str, settings: Settings) -> None:
    await _get_session_store(settings).touch(token, settings.web_session_ttl_seconds)


async def _is_session_active(token: str, settings: Settings) -> bool:
    return await _get_session_store(settings).is_active(token)


async def _require_auth(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    """Verifica se o usuário está autenticado via sessão de login."""
    session_token = request.cookies.get(LOGIN_SESSION_COOKIE)

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login necessário",
        )

    # Validar se o token está nas sessões ativas
    if not await _is_session_active(session_token, settings):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada",
        )
    await _touch_session(session_token, settings)


@router.get("/", response_class=HTMLResponse)
async def get_home_page(request: Request) -> HTMLResponse:
    """Exibe a página institucional inicial."""
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
        },
    )


@router.get("/web/app", response_class=HTMLResponse)
async def get_web_form(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    """Exibe o formulário web principal (requer autenticação)."""
    try:
        await _require_auth(request, settings)
    except HTTPException:
        # Redireciona para login se não autenticado
        csrf_token = _generate_csrf_token()
        response = templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "csrf_token": csrf_token,
                "error": "Login necessário para acessar o sistema",
            },
        )
        _set_csrf_cookie(response, csrf_token, settings)
        return response

    csrf_token = _generate_csrf_token()
    response = templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "csrf_token": csrf_token,
            "timezone": settings.timezone,
            "max_upload": settings.web_max_upload_size,
            "user": {"name": "Usuário"},  # Adicionando variável user que estava faltando
        },
    )
    _set_csrf_cookie(response, csrf_token, settings)
    _refresh_session_cookie(response, settings)
    return response


@router.get("/web/login", response_class=HTMLResponse)
async def get_login_form(
    request: Request,
    error: str | None = None,
) -> HTMLResponse:
    """Exibe o formulário de login."""
    csrf_token = _generate_csrf_token()
    response = templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "csrf_token": csrf_token,
            "error": error,
        },
    )
    _set_csrf_cookie(response, csrf_token, get_settings())
    return response


@router.post("/web/login", response_class=HTMLResponse)
async def process_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    """Processa o login do usuário."""
    # Validar CSRF token
    form_data = {"csrf_token": csrf_token}
    if not _validate_csrf(request, form_data):
        # Se CSRF falhar, reexibir formulário com erro
        new_csrf = _generate_csrf_token()
        context = {
            "request": request,
            "error": "Token de segurança inválido. Tente novamente.",
            "csrf_token": new_csrf,
            "username": username,
        }
        return templates.TemplateResponse("login.html", context, status_code=400)

    # Verificar credenciais (usando as mesmas do HTTP Basic Auth)
    if username != "user" or not secrets.compare_digest(password, settings.web_password):
        new_csrf = _generate_csrf_token()
        context = {
            "request": request,
            "error": "Usuário ou senha incorretos.",
            "csrf_token": new_csrf,
            "username": username,
        }
        return templates.TemplateResponse("login.html", context, status_code=401)

    # Criar sessão de login
    session_token = secrets.token_urlsafe(32)
    # Adicionar token às sessões ativas (com persistência)
    await _add_session(session_token, settings)

    # Redirecionar para a interface principal
    from fastapi.responses import RedirectResponse

    response = RedirectResponse(url="/web/app", status_code=302)

    # Definir cookie de sessão seguro
    # Em desenvolvimento (HTTP), secure deve ser False
    is_development = not settings.environment.startswith("prod")
    response.set_cookie(
        key=LOGIN_SESSION_COOKIE,
        value=session_token,
        max_age=3600 * 8,  # 8 horas
        httponly=True,
        secure=not is_development,  # False em desenvolvimento, True em produção
        samesite="lax",
    )

    return response


@router.post("/web/logout")
async def logout(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Encerra a sessão do usuário."""
    # Remover token das sessões ativas (com persistência)
    session_token = request.cookies.get(LOGIN_SESSION_COOKIE)
    if session_token:
        await _remove_session(session_token, settings)

    from fastapi.responses import RedirectResponse

    response = RedirectResponse(url="/web/login", status_code=302)

    # Remover cookie de sessão
    response.delete_cookie(key=LOGIN_SESSION_COOKIE)

    return response


@router.get("/web", response_class=HTMLResponse)
async def get_web_form(
    request: Request,
    settings: Settings = Depends(get_settings),
    db_session=Depends(get_db_session),
) -> HTMLResponse:
    """Exibe o formulário web principal (requer autenticação)."""
    try:
        await _require_auth(request, settings)
    except HTTPException:
        # Redireciona para login se não autenticado
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "csrf_token": _generate_csrf_token(),
                "error": "Login necessário para acessar o sistema",
            },
        )

    # Busca conversas recentes
    conversations = []
    try:
        conversations = await list_recent_conversations(db_session, limit=10)
    except Exception as e:
        logger.warning("Erro ao buscar conversas recentes", error=str(e))

    csrf_token = _generate_csrf_token()
    response = templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "csrf_token": csrf_token,
            "timezone": settings.timezone,
            "max_upload": settings.web_max_upload_size,
            "user": {"name": "Usuário"},
            "conversations": conversations,
        },
    )
    _set_csrf_cookie(response, csrf_token, settings)
    _refresh_session_cookie(response, settings)
    return response


@router.post("/web", response_class=HTMLResponse)
async def submit_web_form(
    request: Request,
    message: str = Form(""),
    image: UploadFile | None = File(None),
    audio: UploadFile | None = File(None),
    ingestion: IngestionService = Depends(get_ingestion_service),
    settings: Settings = Depends(get_settings),
    csrf_token: str = Form(...),
    db_session=Depends(get_db_session),
) -> HTMLResponse:
    # Verificar autenticação primeiro
    try:
        await _require_auth(request, settings)
    except HTTPException:
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/web/login", status_code=302)

    if not _validate_csrf(request, {"csrf_token": csrf_token}):
        # Busca conversas recentes mesmo em caso de erro
        conversations = []
        try:
            conversations = await list_recent_conversations(db_session, limit=10)
        except Exception as e:
            logger.warning("Erro ao buscar conversas recentes", error=str(e))

        new_token = _generate_csrf_token()
        context = {
            "request": request,
            "sent": False,
            "message": message,
            "error": "Token de segurança inválido. Tente novamente.",
            "timezone": settings.timezone,
            "max_upload": settings.web_max_upload_size,
            "csrf_token": new_token,
            "user": {"name": "Usuário"},
            "conversations": conversations,
        }
        response = templates.TemplateResponse(
            "index.html", context, status_code=status.HTTP_400_BAD_REQUEST
        )
        _set_csrf_cookie(response, new_token, settings)
        _refresh_session_cookie(response, settings)
        return response
    try:
        payload = await _build_web_payload(
            message=message,
            image=image,
            audio=audio,
            settings=settings,
        )
    except ValueError as exc:
        # Busca conversas recentes mesmo em caso de erro
        conversations = []
        try:
            conversations = await list_recent_conversations(db_session, limit=10)
        except Exception as e:
            logger.warning("Erro ao buscar conversas recentes", error=str(e))

        new_token = _generate_csrf_token()
        context = {
            "request": request,
            "sent": False,
            "message": message,
            "error": str(exc),
            "timezone": settings.timezone,
            "max_upload": settings.web_max_upload_size,
            "csrf_token": new_token,
            "user": {"name": "Usuário"},
            "conversations": conversations,
        }
        response = templates.TemplateResponse(
            "index.html", context, status_code=status.HTTP_400_BAD_REQUEST
        )
        _set_csrf_cookie(response, new_token, settings)
        _refresh_session_cookie(response, settings)
        return response

    await ingestion.ingest(payload)

    # Busca conversas recentes após o envio
    conversations = []
    try:
        conversations = await list_recent_conversations(db_session, limit=10)
    except Exception as e:
        logger.warning("Erro ao buscar conversas recentes", error=str(e))

    new_token = _generate_csrf_token()
    response = templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "sent": True,
            "message": "",
            "error": None,
            "timezone": settings.timezone,
            "max_upload": settings.web_max_upload_size,
            "csrf_token": new_token,
            "user": {"name": "Usuário"},
            "conversations": conversations,
        },
    )
    _refresh_session_cookie(response, settings)
    _set_csrf_cookie(response, new_token, settings)
    return response


@router.post("/web/ingest")
async def ingest_web_payload(
    request: Request,
    message: str = Form(""),
    image: UploadFile | None = File(None),
    audio: UploadFile | None = File(None),
    ingestion: IngestionService = Depends(get_ingestion_service),
    settings: Settings = Depends(get_settings),
    _: None = Depends(_require_auth),
    csrf_token: str = Form(...),
) -> JSONResponse:
    if not _validate_csrf(request, {"csrf_token": csrf_token}):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Token de segurança inválido. Tente novamente."},
        )
    try:
        payload = await _build_web_payload(
            message=message,
            image=image,
            audio=audio,
            settings=settings,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    result = await ingestion.ingest(payload) or {}
    new_token = _generate_csrf_token()
    response = JSONResponse(
        {
            "status": "accepted",
            "ingestion": result,
            "attachments": payload.extra_data.get("attachments", []),
            "csrf_token": new_token,
        }
    )
    _set_csrf_cookie(response, new_token, settings)
    _refresh_session_cookie(response, settings)
    return response


__all__ = ["router"]


async def _build_web_payload(
    *,
    message: str,
    image: UploadFile | None,
    audio: UploadFile | None,
    settings: Settings,
) -> ChannelMessage:
    max_size = settings.web_max_upload_size
    attachments: list[dict[str, Any]] = []
    upload_dir: Path | None = None

    if image and image.filename:
        upload_dir = upload_dir or _ensure_upload_dir(settings.web_upload_dir)
        attachments.append(
            await _persist_upload(
                image,
                upload_dir,
                allowed_prefixes=("image/",),
                max_size=max_size,
            )
        )

    if audio and audio.filename:
        upload_dir = upload_dir or _ensure_upload_dir(settings.web_upload_dir)
        attachments.append(
            await _persist_upload(
                audio,
                upload_dir,
                allowed_prefixes=("audio/",),
                max_size=max_size,
            )
        )

    text = message.strip()
    if not text and not attachments:
        raise ValueError("Digite uma mensagem ou anexe um arquivo.")
    if not text:
        text = "Entrada multimodal recebida via Web UI"
    if len(text) > settings.ingestion_max_content_length:
        raise ValueError(
            f"Mensagem excede o limite de {settings.ingestion_max_content_length} caracteres."
        )

    return ChannelMessage(
        channel=Channel.WEB,
        sender="web-ui",
        content=text,
        extra_data={"attachments": attachments},
    )


def _ensure_upload_dir(directory: str) -> Path:
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


async def _persist_upload(
    file: UploadFile,
    directory: Path,
    *,
    allowed_prefixes: tuple[str, ...],
    max_size: int,
) -> dict[str, Any]:
    content_type = file.content_type or ""
    if allowed_prefixes and not any(content_type.startswith(prefix) for prefix in allowed_prefixes):
        raise ValueError("Tipo de arquivo não suportado.")

    data = await file.read()
    if not data:
        raise ValueError("Arquivo vazio.")
    if len(data) > max_size:
        raise ValueError("Arquivo excede o limite permitido.")

    suffix = Path(file.filename or "upload").suffix
    if not suffix and content_type.startswith("audio/"):
        suffix = ".webm"

    filename = f"{uuid4().hex}{suffix}"
    destination = directory / filename
    destination.write_bytes(data)
    await file.close()
    logger.info("web_upload_stored", filename=filename, content_type=content_type, size=len(data))

    return {
        "path": str(destination),
        "original_name": file.filename or filename,
        "content_type": content_type,
        "size": len(data),
    }


def _generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def _set_csrf_cookie(response: Response, token: str, settings: Settings) -> None:
    secure = settings.environment == "production"
    response.set_cookie(
        CSRF_COOKIE,
        token,
        max_age=3600,
        httponly=False,
        samesite="lax",
        secure=secure,
    )


def _validate_csrf(request: Request, form_data: dict) -> bool:
    """Valida token CSRF."""
    cookie_token = request.cookies.get("sparkone_csrftoken")
    form_token = form_data.get("csrf_token")  # Corrigido para usar o nome correto
    header_token = request.headers.get("X-CSRFToken")

    # Usar token do form ou header
    candidate = form_token or header_token

    return cookie_token and candidate and cookie_token == candidate


def _validate_session_cookie(request: Request, settings: Settings) -> None:
    cookie = request.cookies.get(SESSION_COOKIE)
    if not cookie:
        return
    try:
        issued_at = datetime.fromisoformat(cookie)
    except ValueError:
        issued_at = None
    if issued_at is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão expirada",
            headers={"WWW-Authenticate": "Basic"},
        )
    if issued_at.tzinfo is None:
        issued_at = issued_at.replace(tzinfo=UTC)
    lifetime = (datetime.now(UTC) - issued_at).total_seconds()
    if lifetime > settings.web_session_ttl_seconds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão expirada",
            headers={"WWW-Authenticate": "Basic"},
        )


def _refresh_session_cookie(response: Response, settings: Settings) -> None:
    issued_at = datetime.now(UTC).isoformat()
    secure = settings.environment == "production"
    response.set_cookie(
        SESSION_COOKIE,
        issued_at,
        max_age=settings.web_session_ttl_seconds,
        httponly=True,
        samesite="lax",
        secure=secure,
    )
