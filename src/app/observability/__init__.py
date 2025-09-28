"""Observability helpers (tracing, metrics, logging)."""

from .tracing import instrument_application

__all__ = ["instrument_application"]
