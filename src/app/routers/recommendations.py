"""Recommendations API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.recommendations import RecommendationsService


def _get_service() -> RecommendationsService:
    return RecommendationsService()


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/places")
async def get_places(
    q: str = Query(..., description="Search query (e.g., 'cafés', 'academias')"),
    lat: float | None = Query(None, description="Latitude para refinar resultados"),
    lng: float | None = Query(None, description="Longitude para refinar resultados"),
    radius_m: int = Query(4000, ge=100, le=50000),
    limit: int = Query(10, ge=1, le=50),
    svc: RecommendationsService = Depends(_get_service),
) -> dict:
    try:
        return await svc.search_places(q, lat=lat, lng=lng, radius_m=radius_m, limit=limit)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - external failure path
        raise HTTPException(status_code=502, detail=f"Recommendations provider error: {exc}")


__all__ = ["router"]

