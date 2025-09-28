"""Channel-specific ingestion endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.channels import ChannelNotRegisteredError, MessageNormalizer
from app.core.validators import SecureWebhookPayload
from app.dependencies import get_ingestion_service, get_message_normalizer
from app.models.schemas import ChannelMessage
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/channels", tags=["channels"])
logger = logging.getLogger(__name__)


@router.post("/{channel_name}", status_code=status.HTTP_202_ACCEPTED)
async def ingest_channel_payload(
    channel_name: str,
    payload: SecureWebhookPayload,
    normalizer: MessageNormalizer = Depends(get_message_normalizer),
    ingestion: IngestionService = Depends(get_ingestion_service),
) -> dict[str, str]:
    """Accept raw payload from specific channels and normalize it.

    This endpoint now includes robust input validation and sanitization.
    """

    # Validar nome do canal
    if not channel_name or not isinstance(channel_name, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Nome do canal inválido"
        )

    # Sanitizar nome do canal
    import re

    if not re.match(r"^[a-zA-Z0-9_-]+$", channel_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome do canal deve conter apenas letras, números, underscore e hífen",
        )

    channel_name = channel_name.lower().strip()

    # Log da tentativa (sem dados sensíveis)
    logger.info(f"Channel ingestion attempt: {channel_name}")

    try:
        # Usar payload já sanitizado
        normalized: ChannelMessage = await normalizer.normalize(channel_name, payload.payload)

    except ChannelNotRegisteredError as exc:
        logger.warning(f"Unregistered channel attempted: {channel_name}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        logger.warning(f"Channel normalization error for {channel_name}: {str(exc)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Unexpected error normalizing {channel_name}: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
        ) from exc

    try:
        await ingestion.ingest(normalized)
        logger.info(f"Channel message ingested successfully: {channel_name}")

    except ValueError as exc:
        logger.warning(f"Ingestion validation error for {channel_name}: {str(exc)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Unexpected error during ingestion for {channel_name}: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
        ) from exc

    return {"status": "accepted", "channel": normalized.channel.value}


__all__ = ["router"]
