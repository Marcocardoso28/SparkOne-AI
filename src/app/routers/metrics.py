"""Expose Prometheus metrics."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import generate_latest

router = APIRouter(tags=["metrics"], include_in_schema=False)


@router.get("/metrics")
async def metrics_endpoint() -> Response:
    data = generate_latest()
    # Forçar content-type exato sem charset (alguns testes validam igualdade)
    return Response(content=data, headers={"content-type": "text/plain; version=0.0.4"})


__all__ = ["router"]
