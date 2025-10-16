"""SparkOne FastAPI application bootstrap."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import get_settings
from .core.logging import configure_logging
from .core.startup import register_startup_validations
from .api.dependencies import get_evolution_client, get_notion_client
from .middleware.correlation import CorrelationIdMiddleware
from .middleware.metrics import PrometheusMiddleware
from .middleware.rate_limiting import RateLimitMiddleware, resolve_rate_limit_store
from .middleware.security_headers import SecurityHeadersMiddleware
from .middleware.security_logging import SecurityLoggingMiddleware
from .observability import instrument_application
from .api.v1 import (
    alerts,
    auth,
    brief,
    channels,
    events,
    health,
    ingest,
    metrics,
    profiler,
    storage_configs,
    tasks,
    web,
    webhooks,
)


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@asynccontextmanager
async def _lifespan(app: FastAPI):
    # Startup
    from .core.startup import validate_configuration

    await validate_configuration()

    try:
        yield
    finally:
        evolution = get_evolution_client()
        if evolution is not None:
            await evolution.close()
        notion = get_notion_client()
        if notion is not None:
            await notion.close()


def create_application() -> FastAPI:
    """Instantiate the FastAPI application with configured routers."""

    settings = get_settings()
    configure_logging(debug=settings.debug)
    app = FastAPI(
        title="SparkOne API",
        version="0.1.0",
        debug=settings.debug,
        lifespan=_lifespan,
    )
    register_startup_validations(app)
    instrument_application(app, settings)

    allowed_hosts = _split_csv(settings.allowed_hosts)
    if allowed_hosts and allowed_hosts != ["*"]:
        # Garantir que healthchecks internos e chamadas locais funcionem
        safe_hosts = set(allowed_hosts)
        safe_hosts.update({"localhost", "127.0.0.1", "::1"})
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(safe_hosts))

    cors_origins = _split_csv(settings.cors_origins) or ["*"]
    cors_methods = _split_csv(settings.cors_allow_methods) or ["*"]
    cors_headers = _split_csv(settings.cors_allow_headers) or ["*"]

    # Configuração CORS segura - não permitir * com credenciais em produção
    if settings.environment == "production" and cors_origins == ["*"]:
        cors_origins = ["https://sparkone.macspark.dev",
                        "https://app.sparkone.com"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=settings.cors_allow_credentials
        and settings.environment != "production"
        or cors_origins != ["*"],
        allow_methods=["*"] if cors_methods == ["*"] else cors_methods,
        allow_headers=["*"] if cors_headers == ["*"] else cors_headers,
    )
    app.add_middleware(CorrelationIdMiddleware)

    # Rate limiting middleware - ajustado para desenvolvimento
    if settings.environment == "development":
        # Limites mais permissivos para desenvolvimento
        endpoint_limits = {
            # 50 tentativas por 5 min
            "/web/login": {"requests": 50, "window": 300},
            "/web/logout": {"requests": 100, "window": 300},  # 100 por 5 min
            "/ingest": {"requests": 500, "window": 3600},  # 500 por hora
            "/channels/": {"requests": 300, "window": 3600},  # 300 por hora
            "/webhooks/": {"requests": 1000, "window": 3600},  # 1000 por hora
            "/web": {"requests": 2000, "window": 3600},  # 2000 por hora
            "/web/ingest": {"requests": 1000, "window": 3600},  # 1000 por hora
            "/health": {"requests": 10000, "window": 3600},  # 10000 por hora
            "/metrics": {"requests": 5000, "window": 3600},  # 5000 por hora
        }
    else:
        # Limites mais restritivos para produção
        endpoint_limits = {
            # 5 tentativas por 15 min
            "/web/login": {"requests": 5, "window": 900},
            "/web/logout": {"requests": 10, "window": 300},  # 10 por 5 min
            "/ingest": {"requests": 50, "window": 3600},  # 50 por hora
            "/channels/": {"requests": 30, "window": 3600},  # 30 por hora
            "/webhooks/": {"requests": 100, "window": 3600},  # 100 por hora
            "/web": {"requests": 200, "window": 3600},  # 200 por hora
            "/web/ingest": {"requests": 100, "window": 3600},  # 100 por hora
            "/health": {"requests": 1000, "window": 3600},  # 1000 por hora
            "/metrics": {"requests": 500, "window": 3600},  # 500 por hora
        }

    rate_limit_store = resolve_rate_limit_store(settings.redis_url)
    app.add_middleware(
        RateLimitMiddleware,
        store=rate_limit_store,
        default_requests=1000 if settings.environment == "development" else 100,
        default_window=3600,
        endpoint_limits=endpoint_limits,
    )

    # Security logging middleware para auditoria
    app.add_middleware(SecurityLoggingMiddleware)

    app.add_middleware(PrometheusMiddleware)
    app.add_middleware(
        SecurityHeadersMiddleware,
        enable_hsts=settings.security_hsts_enabled and settings.environment == "production",
        hsts_max_age=settings.security_hsts_max_age,
        hsts_include_subdomains=settings.security_hsts_include_subdomains,
        hsts_preload=settings.security_hsts_preload,
    )
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(ingest.router)
    app.include_router(channels.router)
    app.include_router(web.router)
    app.include_router(webhooks.router)
    app.include_router(brief.router)
    app.include_router(tasks.router)
    app.include_router(events.router)
    app.include_router(storage_configs.router, prefix="/api/v1")
    app.include_router(metrics.router)
    app.include_router(alerts.router)
    app.include_router(profiler.router)

    # Root path is served by web router (home page)

    static_dir = Path(__file__).resolve().parent / "web" / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    return app


app = create_application()


__all__ = ["app", "create_application"]
