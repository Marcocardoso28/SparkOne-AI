"""Endpoints for message ingestion."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.validators import SecureChannelMessage
from app.dependencies import get_ingestion_service
from app.models.schemas import ChannelMessage
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/ingest", tags=["ingestion"])
logger = logging.getLogger(__name__)


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def ingest_message(
    payload: SecureChannelMessage,
    ingestion: IngestionService = Depends(get_ingestion_service),
) -> dict[str, str]:
    """Receive a normalized channel payload and acknowledge receipt.

    The real orchestration pipeline will route the payload to Agno. In the MVP
    we simply acknowledge that the message has been accepted.

    This endpoint now includes robust input validation and sanitization.
    """

    # Log da tentativa de ingestão (sem dados sensíveis)
    logger.info(
        f"Ingestion attempt from channel: {payload.channel}, sender: {payload.sender[:10]}..."
    )

    try:
        # Converter para o modelo interno
        channel_message = ChannelMessage(
            channel=payload.channel,
            sender=payload.sender,
            content=payload.content,
            message_type=payload.message_type,
            extra_data=payload.extra_data,
        )

        await ingestion.ingest(channel_message)

        logger.info(f"Message ingested successfully from {payload.channel}")

    except ValueError as exc:
        logger.warning(f"Ingestion validation error: {str(exc)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Unexpected error during ingestion: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
        ) from exc

    return {"status": "accepted", "channel": payload.channel}
