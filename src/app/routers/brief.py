"""Endpoints that expose SparkOne briefs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_brief_service
from ..services.brief import BriefService

router = APIRouter(prefix="/brief", tags=["brief"])


@router.get("/structured")
async def get_structured_brief(service: BriefService = Depends(get_brief_service)) -> dict:
    return await service.structured_brief()


@router.get("/text")
async def get_text_brief(service: BriefService = Depends(get_brief_service)) -> dict:
    text = await service.textual_brief()
    return {"brief": text}


__all__ = ["router"]
