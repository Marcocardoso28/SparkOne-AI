"""Incoming webhooks from external providers."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from ..channels import MessageNormalizer
from ..dependencies import get_message_normalizer, get_ingestion_service
from ..services.ingestion import IngestionService

router = APIRouter(prefix="/webhooks", tags=["webhooks"], include_in_schema=False)


@router.post("/whatsapp", status_code=status.HTTP_202_ACCEPTED)
async def whatsapp_webhook(
    payload: dict[str, Any],
    normalizer: MessageNormalizer = Depends(get_message_normalizer),
    ingestion: IngestionService = Depends(get_ingestion_service),
) -> dict[str, str]:
    message = await normalizer.normalize("whatsapp", payload)
    try:
        await ingestion.ingest(message)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"status": "accepted"}


__all__ = ["router"]
