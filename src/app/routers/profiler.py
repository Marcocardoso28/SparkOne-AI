"""
Router para endpoints de profiling e análise de performance.
Fornece acesso às métricas coletadas pelo sistema de profiling.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.profiler import (
    analyze_slow_queries,
    db_profiler,
    get_profiler_stats,
)


# Função temporária para substituir autenticação
def get_current_user():
    return {"id": "temp_user", "username": "temp"}


# Removendo import de auth por enquanto - usar autenticação simples se necessário
# from ..core.auth import get_current_user

router = APIRouter(prefix="/profiler", tags=["profiler"])
logger = logging.getLogger(__name__)


@router.get("/stats", response_model=dict[str, Any])
async def get_performance_stats(current_user: dict = Depends(get_current_user)) -> dict[str, Any]:
    """
    Retorna estatísticas atuais de performance do sistema.
    Endpoint protegido - apenas usuários autenticados.
    """
    try:
        stats = get_profiler_stats()
        logger.info(f"Performance stats requested by user: {current_user.get('id', 'unknown')}")
        return {
            "status": "success",
            "data": stats,
            "message": "Performance statistics retrieved successfully",
        }
    except Exception as e:
        logger.error(f"Error retrieving performance stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance statistics")


@router.get("/report", response_model=dict[str, Any])
async def get_performance_report(
    last_n_queries: int | None = Query(
        None, ge=1, le=10000, description="Número de queries recentes a analisar"
    ),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Gera relatório detalhado de performance.

    Args:
        last_n_queries: Limita análise às N queries mais recentes
    """
    try:
        report = db_profiler.get_performance_report(last_n_queries)

        # Converter para formato serializável
        report_data = {
            "total_queries": report.total_queries,
            "slow_queries": report.slow_queries,
            "slow_query_percentage": round(report.slow_query_percentage, 2),
            "avg_duration": round(report.avg_duration, 4),
            "max_duration": round(report.max_duration, 4),
            "total_memory_usage": round(report.total_memory_usage, 2),
            "avg_cpu_usage": round(report.avg_cpu_usage, 2),
            "queries_by_table": report.queries_by_table,
            "queries_by_operation": report.queries_by_operation,
            "top_slow_queries": [
                {
                    "query": q.query[:300],  # Limitar tamanho
                    "duration": round(q.duration, 4),
                    "table": q.table,
                    "operation": q.operation,
                    "query_type": q.query_type,
                    "memory_delta": round(q.memory_delta, 2),
                    "cpu_percent": round(q.cpu_percent, 2),
                    "timestamp": q.timestamp,
                    "row_count": q.row_count,
                }
                for q in report.top_slow_queries
            ],
        }

        logger.info(f"Performance report generated for user: {current_user.get('id', 'unknown')}")
        return {
            "status": "success",
            "data": report_data,
            "message": f"Performance report generated for {report.total_queries} queries",
        }

    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate performance report")


@router.get("/slow-queries", response_model=dict[str, Any])
async def get_slow_queries(
    threshold: float = Query(
        0.5, ge=0.1, le=10.0, description="Threshold em segundos para considerar query lenta"
    ),
    limit: int = Query(20, ge=1, le=100, description="Número máximo de queries a retornar"),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Analisa e retorna queries lentas baseado no threshold especificado.

    Args:
        threshold: Tempo mínimo em segundos para considerar uma query lenta
        limit: Número máximo de queries a retornar
    """
    try:
        slow_queries = await analyze_slow_queries(threshold)

        # Limitar resultados
        limited_queries = slow_queries[:limit]

        # Converter para formato serializável
        queries_data = [
            {
                "query": q.query[:500],  # Limitar tamanho da query
                "duration": round(q.duration, 4),
                "table": q.table,
                "operation": q.operation,
                "query_type": q.query_type,
                "memory_before": round(q.memory_before, 2),
                "memory_after": round(q.memory_after, 2),
                "memory_delta": round(q.memory_delta, 2),
                "cpu_percent": round(q.cpu_percent, 2),
                "timestamp": q.timestamp,
                "row_count": q.row_count,
                "has_stack_trace": len(q.stack_trace) > 0,
            }
            for q in limited_queries
        ]

        logger.info(
            f"Slow queries analysis completed: {len(limited_queries)} queries found "
            f"(threshold: {threshold}s) for user: {current_user.get('id', 'unknown')}"
        )

        return {
            "status": "success",
            "data": {
                "threshold_seconds": threshold,
                "total_slow_queries": len(slow_queries),
                "returned_queries": len(limited_queries),
                "queries": queries_data,
            },
            "message": f"Found {len(slow_queries)} slow queries (showing {len(limited_queries)})",
        }

    except Exception as e:
        logger.error(f"Error analyzing slow queries: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze slow queries")


@router.get("/query-details/{query_index}", response_model=dict[str, Any])
async def get_query_details(
    query_index: int, current_user: dict = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Retorna detalhes completos de uma query específica pelo índice.

    Args:
        query_index: Índice da query na lista de perfis (0-based)
    """
    try:
        if query_index < 0 or query_index >= len(db_profiler.query_profiles):
            raise HTTPException(status_code=404, detail=f"Query index {query_index} not found")

        query_profile = db_profiler.query_profiles[query_index]

        # Converter para formato detalhado
        query_data = {
            "query": query_profile.query,
            "duration": round(query_profile.duration, 4),
            "table": query_profile.table,
            "operation": query_profile.operation,
            "query_type": query_profile.query_type,
            "memory_before": round(query_profile.memory_before, 2),
            "memory_after": round(query_profile.memory_after, 2),
            "memory_delta": round(query_profile.memory_delta, 2),
            "cpu_percent": round(query_profile.cpu_percent, 2),
            "timestamp": query_profile.timestamp,
            "row_count": query_profile.row_count,
            "parameters": query_profile.parameters,
            "is_slow": query_profile.is_slow,
            "stack_trace": query_profile.stack_trace if query_profile.is_slow else [],
        }

        logger.info(
            f"Query details retrieved for index {query_index} by user: {current_user.get('id', 'unknown')}"
        )

        return {
            "status": "success",
            "data": query_data,
            "message": f"Query details retrieved for index {query_index}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving query details: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve query details")


@router.post("/reset", response_model=dict[str, str])
async def reset_profiler_stats(current_user: dict = Depends(get_current_user)) -> dict[str, str]:
    """
    Limpa todas as estatísticas coletadas pelo profiler.
    Operação administrativa - requer autenticação.
    """
    try:
        db_profiler.reset_stats()

        logger.warning(f"Profiler stats reset by user: {current_user.get('id', 'unknown')}")

        return {"status": "success", "message": "Profiler statistics have been reset"}

    except Exception as e:
        logger.error(f"Error resetting profiler stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset profiler statistics")


@router.post("/toggle", response_model=dict[str, str])
async def toggle_profiler(
    enable: bool = Query(description="True para habilitar, False para desabilitar"),
    current_user: dict = Depends(get_current_user),
) -> dict[str, str]:
    """
    Habilita ou desabilita o profiler.
    Operação administrativa - requer autenticação.
    """
    try:
        if enable:
            db_profiler.enable()
            action = "enabled"
        else:
            db_profiler.disable()
            action = "disabled"

        logger.info(f"Profiler {action} by user: {current_user.get('id', 'unknown')}")

        return {"status": "success", "message": f"Profiler has been {action}"}

    except Exception as e:
        logger.error(f"Error toggling profiler: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle profiler")


@router.get("/health", response_model=dict[str, Any])
async def profiler_health() -> dict[str, Any]:
    """
    Endpoint de health check para o sistema de profiling.
    Não requer autenticação - usado para monitoramento.
    """
    try:
        stats = get_profiler_stats()

        # Determinar status de saúde baseado nas métricas
        health_status = "healthy"
        issues = []

        if stats["slow_query_percentage"] > 20:
            health_status = "warning"
            issues.append(f"High percentage of slow queries: {stats['slow_query_percentage']:.1f}%")

        if stats["avg_duration"] > 1.0:
            health_status = "warning"
            issues.append(f"High average query duration: {stats['avg_duration']:.3f}s")

        if stats["memory_usage_mb"] > 1000:  # 1GB
            health_status = "warning"
            issues.append(f"High memory usage: {stats['memory_usage_mb']:.1f}MB")

        if stats["slow_query_percentage"] > 50 or stats["avg_duration"] > 2.0:
            health_status = "critical"

        return {
            "status": health_status,
            "enabled": stats["enabled"],
            "total_queries": stats["total_queries"],
            "slow_queries": stats["slow_queries"],
            "issues": issues,
            "message": f"Profiler is {health_status}",
        }

    except Exception as e:
        logger.error(f"Error checking profiler health: {e}")
        return {"status": "error", "message": "Failed to check profiler health", "error": str(e)}
