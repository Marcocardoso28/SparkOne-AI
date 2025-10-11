"""Incoming webhooks from external providers."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.channels import MessageNormalizer
from app.core.validators import SecureWebhookPayload
from app.api.dependencies import get_ingestion_service, get_message_normalizer
from app.domain.services.ingestion import IngestionService

router = APIRouter(prefix="/webhooks", tags=["webhooks"], include_in_schema=False)
logger = logging.getLogger(__name__)


@router.post("/whatsapp", status_code=status.HTTP_202_ACCEPTED)
async def whatsapp_webhook(
    payload: SecureWebhookPayload,
    normalizer: MessageNormalizer = Depends(get_message_normalizer),
    ingestion: IngestionService = Depends(get_ingestion_service),
) -> dict[str, str]:
    """WhatsApp webhook endpoint with robust input validation."""

    # Log da tentativa (sem dados sensíveis)
    logger.info("WhatsApp webhook received")

    try:
        # Usar payload já sanitizado
        message = await normalizer.normalize("whatsapp", payload.payload)
        logger.info("WhatsApp message normalized successfully")

    except ValueError as exc:
        logger.warning(f"WhatsApp normalization error: {str(exc)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Unexpected error normalizing WhatsApp message: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
        ) from exc

    try:
        await ingestion.ingest(message)
        logger.info("WhatsApp message ingested successfully")

    except ValueError as exc:
        logger.warning(f"WhatsApp ingestion validation error: {str(exc)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Unexpected error during WhatsApp ingestion: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
        ) from exc

    return {"status": "accepted"}


__all__ = ["router"]
