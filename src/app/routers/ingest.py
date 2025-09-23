"""Endpoints for message ingestion."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ..models.schemas import ChannelMessage
from ..dependencies import get_ingestion_service
from ..services.ingestion import IngestionService

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def ingest_message(
    payload: ChannelMessage,
    ingestion: IngestionService = Depends(get_ingestion_service),
) -> dict[str, str]:
    """Receive a normalized channel payload and acknowledge receipt.

    The real orchestration pipeline will route the payload to Agno. In the MVP
    we simply acknowledge that the message has been accepted.
    """

    try:
        await ingestion.ingest(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"status": "accepted", "channel": payload.channel.value}
