"""Endpoint para receber alertas (ex.: Alertmanager)."""

from __future__ import annotations

from fastapi import APIRouter, status

from ..services.alerts import AlertPayload, forward_alerts_to_whatsapp

router = APIRouter(prefix="/alerts", tags=["alerts"], include_in_schema=False)


@router.post("/alertmanager", status_code=status.HTTP_202_ACCEPTED)
async def alertmanager_webhook(payload: AlertPayload) -> dict[str, str]:
    await forward_alerts_to_whatsapp(payload)
    return {"status": "accepted"}


__all__ = ["router"]
