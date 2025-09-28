"""OpenTelemetry tracing helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_NAMESPACE, SERVICE_VERSION, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
    from opentelemetry.sdk.trace.sampling import ALWAYS_ON, TraceIdRatioBased
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    trace = None  # type: ignore[assignment]

    def instrument_application(*_args, **_kwargs):  # type: ignore[override]
        """Fallback when OpenTelemetry packages are missing."""

        logger = structlog.get_logger(__name__)
        logger.warning("opentelemetry_not_installed", action="skipping_tracing")

    __all__ = ["instrument_application"]
else:
    if TYPE_CHECKING:
        from fastapi import FastAPI

        from ..config import Settings

    logger = structlog.get_logger(__name__)
    _instrumented = False

    def _parse_headers(raw: str | None) -> dict[str, str]:
        if not raw:
            return {}
        headers: dict[str, str] = {}
        for pair in raw.split(","):
            if ":" not in pair:
                continue
            key, value = pair.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key:
                headers[key] = value
        return headers

    def instrument_application(app: "FastAPI", settings: "Settings") -> None:
        """Configure tracing exporters and instrument integrations."""

        global _instrumented
        if _instrumented:
            return
        if not settings.otel_enabled:
            logger.info("otel_disabled", reason="flag_off")
            return
        if settings.environment == "test":
            logger.info("otel_disabled", reason="test_environment")
            return
        if trace is None:  # safety, though guarded in import
            logger.warning("otel_unavailable", reason="missing_dependencies")
            return

        sample_ratio = max(0.0, min(settings.otel_traces_sampler_ratio, 1.0))
        sampler = ALWAYS_ON if sample_ratio >= 1.0 else TraceIdRatioBased(sample_ratio)

        resource = Resource.create(
            {
                SERVICE_NAME: settings.otel_service_name,
                SERVICE_NAMESPACE: settings.otel_service_namespace,
                SERVICE_VERSION: app.version,
                "deployment.environment": settings.environment,
            }
        )

        provider = TracerProvider(resource=resource, sampler=sampler)

        if settings.otel_exporter_endpoint:
            headers = _parse_headers(settings.otel_exporter_headers)
            exporter = OTLPSpanExporter(
                endpoint=settings.otel_exporter_endpoint,
                headers=headers,
            )
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info(
                "otel_exporter_configured",
                endpoint=settings.otel_exporter_endpoint,
                headers=bool(headers),
            )
        if settings.otel_debug_console:
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
            logger.warning("otel_console_export_enabled")

        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(app)
        HTTPXClientInstrumentor().instrument()
        AsyncPGInstrumentor().instrument()
        RedisInstrumentor().instrument()

        _instrumented = True
        logger.info("otel_instrumented", sampler_ratio=sample_ratio)

    __all__ = ["instrument_application"]
