"""Channel-specific ingestion endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from ..channels import ChannelNotRegisteredError, MessageNormalizer
from ..dependencies import get_ingestion_service, get_message_normalizer
from ..models.schemas import ChannelMessage
from ..services.ingestion import IngestionService

router = APIRouter(prefix="/channels", tags=["channels"])


@router.post("/{channel_name}", status_code=status.HTTP_202_ACCEPTED)
async def ingest_channel_payload(
    channel_name: str,
    payload: dict[str, Any],
    normalizer: MessageNormalizer = Depends(get_message_normalizer),
    ingestion: IngestionService = Depends(get_ingestion_service),
) -> dict[str, str]:
    """Accept raw payload from specific channels and normalize it."""

    try:
        normalized: ChannelMessage = await normalizer.normalize(channel_name, payload)
    except ChannelNotRegisteredError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        await ingestion.ingest(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"status": "accepted", "channel": normalized.channel.value}


__all__ = ["router"]
