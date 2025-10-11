"""Endpoints for message ingestion."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.validators import SecureChannelMessage
from app.api.dependencies import get_ingestion_service
from app.models.schemas import ChannelMessage
from app.domain.services.ingestion import IngestionService
from pydantic import BaseModel

router = APIRouter(prefix="/ingest", tags=["ingestion"])
logger = logging.getLogger(__name__)


class SimpleIngestRequest(BaseModel):
    """Simple ingest request model for testing."""
    message: str
    channel: str
    sender: str
    timestamp: str | None = None


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def ingest_message(
    payload: SimpleIngestRequest,
    ingestion: IngestionService = Depends(get_ingestion_service),
) -> dict[str, str]:
    """Simple ingest endpoint for testing."""

    # Convert to secure format
    try:
        channel_message = ChannelMessage(
            channel=payload.channel,
            sender=payload.sender,
            content=payload.message,
            message_type="free_text",
            extra_data={}
        )

        await ingestion.ingest(channel_message)

    except Exception as exc:
        logger.error(f"Error during simple ingestion: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) from exc

    return {"status": "accepted", "channel": payload.channel}
