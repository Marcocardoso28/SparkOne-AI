"""Middleware de logging de segurança para auditoria e monitoramento."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any
from uuid import uuid4

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Logger específico para eventos de segurança
security_logger = structlog.get_logger("security")
audit_logger = structlog.get_logger("audit")


class SecurityEvent:
    """Representa um evento de segurança."""

    # Tipos de eventos de segurança
    LOGIN_ATTEMPT = "login_attempt"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    VALIDATION_ERROR = "validation_error"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    FILE_UPLOAD = "file_upload"
    API_ACCESS = "api_access"
    CSRF_VIOLATION = "csrf_violation"
    UNAUTHORIZED_ACCESS = "unauthorized_access"

    def __init__(
        self,
        event_type: str,
        user_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        endpoint: str | None = None,
        method: str | None = None,
        details: dict[str, Any] | None = None,
        severity: str = "info",
    ):
        self.event_id = str(uuid4())
        self.timestamp = time.time()
        self.event_type = event_type
        self.user_id = user_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.endpoint = endpoint
        self.method = method
        self.details = details or {}
        self.severity = severity  # info, warning, error, critical

    def to_dict(self) -> dict[str, Any]:
        """Converte evento para dicionário."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "endpoint": self.endpoint,
            "method": self.method,
            "details": self.details,
            "severity": self.severity,
        }


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging de eventos de segurança."""

    def __init__(self, app):
        super().__init__(app)
        self.sensitive_endpoints = {"/web/login", "/web/logout", "/ingest", "/webhooks/whatsapp"}
        self.sensitive_headers = {"authorization", "cookie", "x-api-key", "x-auth-token"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Processa request com logging de segurança."""

        # Gerar ID único para a request
        request_id = str(uuid4())

        # Extrair informações da request
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        endpoint = request.url.path
        method = request.method

        # Obter ID do usuário se disponível
        user_id = self._extract_user_id(request)

        # Log da request de entrada (apenas para endpoints sensíveis)
        if self._is_sensitive_endpoint(endpoint):
            self._log_request_start(request_id, client_ip, user_agent, endpoint, method, user_id)

        start_time = time.time()

        try:
            # Processar request
            response = await call_next(request)

            # Calcular tempo de processamento
            processing_time = time.time() - start_time

            # Log da resposta
            if self._is_sensitive_endpoint(endpoint):
                self._log_request_end(
                    request_id, response.status_code, processing_time, endpoint, method, user_id
                )

            # Log de eventos específicos baseados na resposta
            self._log_response_events(request, response, client_ip, user_agent, user_id)

            return response

        except Exception as exc:
            # Log de erro
            processing_time = time.time() - start_time

            self._log_request_error(
                request_id, str(exc), processing_time, endpoint, method, user_id, client_ip
            )

            raise

    def _get_client_ip(self, request: Request) -> str:
        """Obtém IP real do cliente."""
        # Tentar headers de proxy primeiro
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _extract_user_id(self, request: Request) -> str | None:
        """Extrai ID do usuário da request."""
        # Tentar obter de cookie de sessão
        session_cookie = request.cookies.get("sparkone_session")
        if session_cookie:
            return f"session:{session_cookie[:8]}"

        # Tentar obter de header de autorização
        auth_header = request.headers.get("authorization")
        if auth_header:
            return f"auth:{auth_header[:8]}"

        return None

    def _is_sensitive_endpoint(self, endpoint: str) -> bool:
        """Verifica se endpoint é sensível."""
        return any(endpoint.startswith(sensitive) for sensitive in self.sensitive_endpoints)

    def _log_request_start(
        self,
        request_id: str,
        client_ip: str,
        user_agent: str,
        endpoint: str,
        method: str,
        user_id: str | None,
    ) -> None:
        """Log do início da request."""
        audit_logger.info(
            "Request started",
            request_id=request_id,
            client_ip=client_ip,
            user_agent=user_agent,
            endpoint=endpoint,
            method=method,
            user_id=user_id,
        )

    def _log_request_end(
        self,
        request_id: str,
        status_code: int,
        processing_time: float,
        endpoint: str,
        method: str,
        user_id: str | None,
    ) -> None:
        """Log do fim da request."""
        audit_logger.info(
            "Request completed",
            request_id=request_id,
            status_code=status_code,
            processing_time_ms=round(processing_time * 1000, 2),
            endpoint=endpoint,
            method=method,
            user_id=user_id,
        )

    def _log_request_error(
        self,
        request_id: str,
        error: str,
        processing_time: float,
        endpoint: str,
        method: str,
        user_id: str | None,
        client_ip: str,
    ) -> None:
        """Log de erro na request."""
        security_logger.error(
            "Request error",
            request_id=request_id,
            error=error,
            processing_time_ms=round(processing_time * 1000, 2),
            endpoint=endpoint,
            method=method,
            user_id=user_id,
            client_ip=client_ip,
        )

    def _log_response_events(
        self,
        request: Request,
        response: Response,
        client_ip: str,
        user_agent: str,
        user_id: str | None,
    ) -> None:
        """Log eventos específicos baseados na resposta."""

        endpoint = request.url.path
        method = request.method
        status_code = response.status_code

        # Login attempts
        if endpoint == "/web/login" and method == "POST":
            if status_code in (200, 302):  # 302 é redirect após login bem-sucedido
                self._log_security_event(
                    SecurityEvent.LOGIN_SUCCESS,
                    user_id=user_id,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    endpoint=endpoint,
                    method=method,
                    severity="info",
                )
            else:
                self._log_security_event(
                    SecurityEvent.LOGIN_FAILURE,
                    user_id=user_id,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    endpoint=endpoint,
                    method=method,
                    details={"status_code": status_code},
                    severity="warning",
                )

        # Logout
        elif endpoint == "/web/logout":
            self._log_security_event(
                SecurityEvent.LOGOUT,
                user_id=user_id,
                ip_address=client_ip,
                user_agent=user_agent,
                endpoint=endpoint,
                method=method,
                severity="info",
            )

        # Rate limiting
        elif status_code == 429:
            self._log_security_event(
                SecurityEvent.RATE_LIMIT_EXCEEDED,
                user_id=user_id,
                ip_address=client_ip,
                user_agent=user_agent,
                endpoint=endpoint,
                method=method,
                severity="warning",
            )

        # Validation errors
        elif status_code == 400:
            self._log_security_event(
                SecurityEvent.VALIDATION_ERROR,
                user_id=user_id,
                ip_address=client_ip,
                user_agent=user_agent,
                endpoint=endpoint,
                method=method,
                details={"status_code": status_code},
                severity="info",
            )

        # Unauthorized access
        elif status_code in (401, 403):
            self._log_security_event(
                SecurityEvent.UNAUTHORIZED_ACCESS,
                user_id=user_id,
                ip_address=client_ip,
                user_agent=user_agent,
                endpoint=endpoint,
                method=method,
                details={"status_code": status_code},
                severity="warning",
            )

        # API access para endpoints de ingestão
        elif endpoint.startswith(("/ingest", "/channels/", "/webhooks/")) and status_code == 200:
            self._log_security_event(
                SecurityEvent.API_ACCESS,
                user_id=user_id,
                ip_address=client_ip,
                user_agent=user_agent,
                endpoint=endpoint,
                method=method,
                severity="info",
            )

    def _log_security_event(self, event_type: str, **kwargs) -> None:
        """Log de evento de segurança."""
        event = SecurityEvent(event_type, **kwargs)

        # Log estruturado
        log_data = event.to_dict()

        if event.severity == "critical":
            security_logger.critical("Security event", **log_data)
        elif event.severity == "error":
            security_logger.error("Security event", **log_data)
        elif event.severity == "warning":
            security_logger.warning("Security event", **log_data)
        else:
            security_logger.info("Security event", **log_data)


def log_security_event(
    event_type: str,
    user_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    endpoint: str | None = None,
    method: str | None = None,
    details: dict[str, Any] | None = None,
    severity: str = "info",
) -> None:
    """Função utilitária para log de eventos de segurança."""
    event = SecurityEvent(
        event_type=event_type,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        endpoint=endpoint,
        method=method,
        details=details,
        severity=severity,
    )

    log_data = event.to_dict()

    if severity == "critical":
        security_logger.critical("Security event", **log_data)
    elif severity == "error":
        security_logger.error("Security event", **log_data)
    elif severity == "warning":
        security_logger.warning("Security event", **log_data)
    else:
        security_logger.info("Security event", **log_data)


def log_file_upload_event(
    filename: str,
    file_size: int,
    mime_type: str,
    user_id: str | None = None,
    ip_address: str | None = None,
    success: bool = True,
) -> None:
    """Log específico para uploads de arquivo."""
    log_security_event(
        SecurityEvent.FILE_UPLOAD,
        user_id=user_id,
        ip_address=ip_address,
        details={
            "filename": filename,
            "file_size": file_size,
            "mime_type": mime_type,
            "success": success,
        },
        severity="info" if success else "warning",
    )


def log_suspicious_activity(
    activity_type: str,
    description: str,
    user_id: str | None = None,
    ip_address: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Log de atividade suspeita."""
    log_security_event(
        SecurityEvent.SUSPICIOUS_ACTIVITY,
        user_id=user_id,
        ip_address=ip_address,
        details={"activity_type": activity_type, "description": description, **(details or {})},
        severity="warning",
    )
