"""Minimal Web UI for manual interactions (text, voice, images)."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates

from ..config import Settings, get_settings
from ..models.schemas import Channel, ChannelMessage
from ..services.ingestion import IngestionService
from ..dependencies import get_ingestion_service

router = APIRouter(tags=["web"], include_in_schema=False)
security = HTTPBasic()
templates = Jinja2Templates(directory="src/app/web/templates")
logger = structlog.get_logger(__name__)

CSRF_COOKIE = "sparkone_csrftoken"
CSRF_HEADER = "X-SparkOne-CSRF"
SESSION_COOKIE = "sparkone_session"


def _require_auth(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    if settings.web_password is None:
        # Sem senha configurada, não validar autenticação
        return
    
    # Com senha configurada, validar credenciais básicas
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais necessárias",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    import base64
    try:
        encoded_credentials = auth_header.split(" ", 1)[1]
        decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
        username, password = decoded_credentials.split(":", 1)
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    if not secrets.compare_digest(password, settings.web_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )
    _validate_session_cookie(request, settings)


@router.get("/web", response_class=HTMLResponse)
async def get_web_form(
    request: Request,
    _: None = Depends(_require_auth),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    csrf_token = _generate_csrf_token()
    context = {
        "request": request,
        "sent": False,
        "message": "",
        "error": None,
        "timezone": settings.timezone,
        "max_upload": settings.web_max_upload_size,
        "csrf_token": csrf_token,
    }
    response = templates.TemplateResponse(request, "index.html", context)
    _set_csrf_cookie(response, csrf_token, settings)
    return response


@router.post("/web", response_class=HTMLResponse)
async def submit_web_form(
    request: Request,
    message: str = Form(""),
    image: UploadFile | None = File(None),
    audio: UploadFile | None = File(None),
    ingestion: IngestionService = Depends(get_ingestion_service),
    _: None = Depends(_require_auth),
    settings: Settings = Depends(get_settings),
    csrf_token: str = Form(...),
) -> HTMLResponse:
    _validate_csrf(request, csrf_token)
    try:
        payload = await _build_web_payload(
            message=message,
            image=image,
            audio=audio,
            settings=settings,
        )
    except ValueError as exc:
        new_token = _generate_csrf_token()
        context = {
            "request": request,
            "sent": False,
            "message": message,
            "error": str(exc),
            "timezone": settings.timezone,
            "max_upload": settings.web_max_upload_size,
            "csrf_token": new_token,
        }
        response = templates.TemplateResponse(request, "index.html", context, status_code=status.HTTP_400_BAD_REQUEST)
        _set_csrf_cookie(response, new_token, settings)
        _refresh_session_cookie(response, settings)
        return response

    await ingestion.ingest(payload)
    new_token = _generate_csrf_token()
    response = templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "sent": True,
            "message": "",
            "error": None,
            "timezone": settings.timezone,
            "max_upload": settings.web_max_upload_size,
            "csrf_token": new_token,
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
    _validate_csrf(request, csrf_token)
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


def _validate_csrf(request: Request, form_token: str | None) -> None:
    cookie_token = request.cookies.get(CSRF_COOKIE)
    header_token = request.headers.get(CSRF_HEADER)
    candidate = form_token or header_token
    if not cookie_token or not candidate or not secrets.compare_digest(cookie_token, candidate):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token inválido.")


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
        issued_at = issued_at.replace(tzinfo=timezone.utc)
    lifetime = (datetime.now(timezone.utc) - issued_at).total_seconds()
    if lifetime > settings.web_session_ttl_seconds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão expirada",
            headers={"WWW-Authenticate": "Basic"},
        )


def _refresh_session_cookie(response: Response, settings: Settings) -> None:
    issued_at = datetime.now(timezone.utc).isoformat()
    secure = settings.environment == "production"
    response.set_cookie(
        SESSION_COOKIE,
        issued_at,
        max_age=settings.web_session_ttl_seconds,
        httponly=True,
        samesite="lax",
        secure=secure,
    )
