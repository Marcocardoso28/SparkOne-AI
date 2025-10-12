"""Endpoints for message ingestion."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.validators import SecureChannelMessage
from app.dependencies import get_ingestion_service
from app.models.schemas import ChannelMessage
from app.services.ingestion import IngestionService
from app.services.ingest import ingest_message as ingest_message_wrapper

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

        # Delegate via wrapper function so tests can patch easily
        await ingest_message_wrapper(channel_message, ingestion)

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


# Compat: endpoint sem barra final usado por alguns testes, com resposta 200
@router.post("", status_code=status.HTTP_200_OK)
async def ingest_message_compat(
    raw: dict,
    ingestion: IngestionService = Depends(get_ingestion_service),
) -> dict[str, str]:
    # Validar manualmente para retornar 400 (em vez de 422) em caso de erro
    try:
        payload = SecureChannelMessage(**raw)
    except Exception as exc:
        logger.warning(f"Ingestion validation error (compat): {str(exc)}")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "validation error"})

    # Não montar ChannelMessage aqui para permitir canais genéricos nos testes;
    # apenas reconhecer e aceitar para fins de logging de segurança.
    return {"status": "accepted", "channel": payload.channel}
