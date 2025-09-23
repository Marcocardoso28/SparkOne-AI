"""SparkOne FastAPI application bootstrap."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import get_settings
from .routers import health, ingest, channels, web, webhooks, brief, tasks, events, metrics, alerts, profiler
from fastapi.responses import RedirectResponse
from .middleware.security import InMemoryRateLimiter
from .middleware.metrics import PrometheusMiddleware
from .middleware.security_headers import SecurityHeadersMiddleware
from .middleware.correlation import CorrelationIdMiddleware
from .core.logging import configure_logging
from .core.startup import register_startup_validations
from .dependencies import get_evolution_client, get_notion_client


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

    allowed_hosts = _split_csv(settings.allowed_hosts)
    if allowed_hosts and allowed_hosts != ["*"]:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

    cors_origins = _split_csv(settings.cors_origins) or ["*"]
    cors_methods = _split_csv(settings.cors_allow_methods) or ["*"]
    cors_headers = _split_csv(settings.cors_allow_headers) or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if cors_origins == ["*"] else cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"] if cors_methods == ["*"] else cors_methods,
        allow_headers=["*"] if cors_headers == ["*"] else cors_headers,
    )
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        InMemoryRateLimiter,
        max_requests=120 if settings.environment == "development" else 60,
        window_seconds=60,
    )
    app.add_middleware(PrometheusMiddleware)
    app.add_middleware(
        SecurityHeadersMiddleware,
        enable_hsts=settings.security_hsts_enabled and settings.environment == "production",
        hsts_max_age=settings.security_hsts_max_age,
        hsts_include_subdomains=settings.security_hsts_include_subdomains,
        hsts_preload=settings.security_hsts_preload,
    )
    app.include_router(health.router)
    app.include_router(ingest.router)
    app.include_router(channels.router)
    app.include_router(web.router)
    app.include_router(webhooks.router)
    app.include_router(brief.router)
    app.include_router(tasks.router)
    app.include_router(events.router)
    app.include_router(metrics.router)
    app.include_router(alerts.router)
    app.include_router(profiler.router)
    
    @app.get("/")
    async def root():
        """Redirect root to web interface."""
        return RedirectResponse(url="/web")
    
    static_dir = Path(__file__).resolve().parent / "web" / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    return app


app = create_application()


__all__ = ["app", "create_application"]
