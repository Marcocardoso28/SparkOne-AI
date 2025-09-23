"""
Módulo de profiling para monitoramento de performance de queries críticas.
Coleta métricas detalhadas de tempo de execução, uso de recursos e gargalos.
"""

import asyncio
import functools
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, TypeVar, Union
from collections import defaultdict
import psutil
import tracemalloc

from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import Counter, Histogram, Gauge

from .metrics import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
)

# Configuração do logger para profiling
profiler_logger = logging.getLogger("sparkone.profiler")

# Métricas específicas de profiling
QUERY_DURATION = Histogram(
    'sparkone_database_query_duration_seconds',
    'Tempo de execução de queries do banco de dados',
    ['query_type', 'table', 'operation']
)

QUERY_COUNT = Counter(
    'sparkone_database_queries_total',
    'Total de queries executadas',
    ['query_type', 'table', 'operation', 'status']
)

MEMORY_USAGE = Gauge(
    'sparkone_memory_usage_bytes',
    'Uso de memória da aplicação',
    ['component']
)

CPU_USAGE = Gauge(
    'sparkone_cpu_usage_percent',
    'Uso de CPU da aplicação',
    ['component']
)

SLOW_QUERIES = Counter(
    'sparkone_slow_queries_total',
    'Queries que excedem o threshold de performance',
    ['query_type', 'threshold']
)

F = TypeVar('F', bound=Callable[..., Any])

@dataclass
class QueryProfile:
    """Perfil detalhado de uma query executada."""
    
    query: str
    duration: float
    table: str
    operation: str
    query_type: str
    memory_before: float
    memory_after: float
    cpu_percent: float
    timestamp: float
    stack_trace: List[str] = field(default_factory=list)
    parameters: Optional[Dict[str, Any]] = None
    row_count: Optional[int] = None
    
    @property
    def memory_delta(self) -> float:
        """Diferença de memória antes/depois da query."""
        return self.memory_after - self.memory_before
    
    @property
    def is_slow(self) -> bool:
        """Verifica se a query é considerada lenta (>500ms)."""
        return self.duration > 0.5


@dataclass
class PerformanceReport:
    """Relatório consolidado de performance."""
    
    total_queries: int
    slow_queries: int
    avg_duration: float
    max_duration: float
    total_memory_usage: float
    avg_cpu_usage: float
    top_slow_queries: List[QueryProfile]
    queries_by_table: Dict[str, int]
    queries_by_operation: Dict[str, int]
    
    @property
    def slow_query_percentage(self) -> float:
        """Percentual de queries lentas."""
        if self.total_queries == 0:
            return 0.0
        return (self.slow_queries / self.total_queries) * 100


class DatabaseProfiler:
    """
    Profiler para monitoramento de performance do banco de dados.
    Coleta métricas detalhadas de queries e recursos utilizados.
    """
    
    def __init__(self, slow_query_threshold: float = 0.5):
        self.slow_query_threshold = slow_query_threshold
        self.query_profiles: List[QueryProfile] = []
        self.enabled = True
        
        # Configurar monitoramento de memória
        tracemalloc.start()
        
        # Registrar event listeners do SQLAlchemy
        self._setup_sqlalchemy_events()
    
    def _setup_sqlalchemy_events(self):
        """Configura event listeners para capturar queries do SQLAlchemy."""
        
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Captura início da execução da query."""
            if not self.enabled:
                return
                
            context._query_start_time = time.time()
            context._memory_before = self._get_memory_usage()
            context._cpu_before = psutil.cpu_percent()
            
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Captura fim da execução da query."""
            if not self.enabled:
                return
                
            duration = time.time() - context._query_start_time
            memory_after = self._get_memory_usage()
            cpu_after = psutil.cpu_percent()
            
            # Analisar a query para extrair informações
            query_info = self._analyze_query(statement)
            
            # Criar perfil da query
            profile = QueryProfile(
                query=statement[:500],  # Limitar tamanho da query
                duration=duration,
                table=query_info['table'],
                operation=query_info['operation'],
                query_type=query_info['query_type'],
                memory_before=context._memory_before,
                memory_after=memory_after,
                cpu_percent=(cpu_after + context._cpu_before) / 2,
                timestamp=time.time(),
                parameters=parameters if isinstance(parameters, dict) else None,
                row_count=cursor.rowcount if hasattr(cursor, 'rowcount') else None
            )
            
            # Adicionar stack trace para queries lentas
            if profile.is_slow:
                profile.stack_trace = traceback.format_stack()
            
            self._record_query_profile(profile)
    
    def _analyze_query(self, statement: str) -> Dict[str, str]:
        """
        Analisa uma query SQL para extrair informações sobre tabela e operação.
        """
        statement_lower = statement.lower().strip()
        
        # Determinar tipo de operação
        if statement_lower.startswith('select'):
            operation = 'SELECT'
            query_type = 'read'
        elif statement_lower.startswith('insert'):
            operation = 'INSERT'
            query_type = 'write'
        elif statement_lower.startswith('update'):
            operation = 'UPDATE'
            query_type = 'write'
        elif statement_lower.startswith('delete'):
            operation = 'DELETE'
            query_type = 'write'
        else:
            operation = 'OTHER'
            query_type = 'other'
        
        # Extrair nome da tabela (simplificado)
        table = 'unknown'
        try:
            if 'from ' in statement_lower:
                parts = statement_lower.split('from ')[1].split()
                if parts:
                    table = parts[0].strip('`"[]')
            elif 'into ' in statement_lower:
                parts = statement_lower.split('into ')[1].split()
                if parts:
                    table = parts[0].strip('`"[]')
            elif 'update ' in statement_lower:
                parts = statement_lower.split('update ')[1].split()
                if parts:
                    table = parts[0].strip('`"[]')
        except (IndexError, AttributeError):
            pass
        
        return {
            'table': table,
            'operation': operation,
            'query_type': query_type
        }
    
    def _get_memory_usage(self) -> float:
        """Obtém uso atual de memória em MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def _record_query_profile(self, profile: QueryProfile):
        """Registra o perfil da query e atualiza métricas."""
        
        # Adicionar à lista de perfis
        self.query_profiles.append(profile)
        
        # Atualizar métricas Prometheus
        QUERY_DURATION.labels(
            query_type=profile.query_type,
            table=profile.table,
            operation=profile.operation
        ).observe(profile.duration)
        
        QUERY_COUNT.labels(
            query_type=profile.query_type,
            table=profile.table,
            operation=profile.operation,
            status='success'
        ).inc()
        
        # Registrar queries lentas
        if profile.is_slow:
            SLOW_QUERIES.labels(
                query_type=profile.query_type,
                threshold='500ms'
            ).inc()
            
            profiler_logger.warning(
                f"Slow query detected: {profile.duration:.3f}s - {profile.query[:100]}..."
            )
        
        # Atualizar métricas de recursos
        MEMORY_USAGE.labels(component='database').set(profile.memory_after)
        CPU_USAGE.labels(component='database').set(profile.cpu_percent)
        
        # Limitar histórico (manter apenas últimas 1000 queries)
        if len(self.query_profiles) > 1000:
            self.query_profiles = self.query_profiles[-1000:]
    
    def get_performance_report(self, last_n_queries: Optional[int] = None) -> PerformanceReport:
        """
        Gera relatório consolidado de performance.
        
        Args:
            last_n_queries: Número de queries recentes a analisar (None = todas)
        """
        queries = self.query_profiles
        if last_n_queries:
            queries = queries[-last_n_queries:]
        
        if not queries:
            return PerformanceReport(
                total_queries=0,
                slow_queries=0,
                avg_duration=0.0,
                max_duration=0.0,
                total_memory_usage=0.0,
                avg_cpu_usage=0.0,
                top_slow_queries=[],
                queries_by_table={},
                queries_by_operation={}
            )
        
        # Calcular estatísticas
        durations = [q.duration for q in queries]
        slow_queries = [q for q in queries if q.is_slow]
        
        # Agrupar por tabela e operação
        queries_by_table = defaultdict(int)
        queries_by_operation = defaultdict(int)
        
        for query in queries:
            queries_by_table[query.table] += 1
            queries_by_operation[query.operation] += 1
        
        # Top 10 queries mais lentas
        top_slow = sorted(slow_queries, key=lambda q: q.duration, reverse=True)[:10]
        
        return PerformanceReport(
            total_queries=len(queries),
            slow_queries=len(slow_queries),
            avg_duration=sum(durations) / len(durations),
            max_duration=max(durations),
            total_memory_usage=sum(q.memory_after for q in queries) / len(queries),
            avg_cpu_usage=sum(q.cpu_percent for q in queries) / len(queries),
            top_slow_queries=top_slow,
            queries_by_table=dict(queries_by_table),
            queries_by_operation=dict(queries_by_operation)
        )
    
    def reset_stats(self):
        """Limpa estatísticas coletadas."""
        self.query_profiles.clear()
        profiler_logger.info("Database profiler stats reset")
    
    def enable(self):
        """Habilita o profiler."""
        self.enabled = True
        profiler_logger.info("Database profiler enabled")
    
    def disable(self):
        """Desabilita o profiler."""
        self.enabled = False
        profiler_logger.info("Database profiler disabled")


# Instância global do profiler
db_profiler = DatabaseProfiler()


def profile_query(func: F) -> F:
    """
    Decorator para profiling de funções que executam queries.
    Adiciona métricas de tempo de execução e uso de recursos.
    """
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        memory_before = db_profiler._get_memory_usage()
        
        try:
            result = await func(*args, **kwargs)
            
            duration = time.time() - start_time
            memory_after = db_profiler._get_memory_usage()
            
            # Registrar métrica de função
            REQUEST_LATENCY.labels(
                method=func.__name__,
                endpoint='database_function'
            ).observe(duration)
            
            if duration > db_profiler.slow_query_threshold:
                profiler_logger.warning(
                    f"Slow function: {func.__name__} took {duration:.3f}s"
                )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            profiler_logger.error(
                f"Function {func.__name__} failed after {duration:.3f}s: {e}"
            )
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        memory_before = db_profiler._get_memory_usage()
        
        try:
            result = func(*args, **kwargs)
            
            duration = time.time() - start_time
            memory_after = db_profiler._get_memory_usage()
            
            # Registrar métrica de função
            REQUEST_LATENCY.labels(
                method=func.__name__,
                endpoint='database_function'
            ).observe(duration)
            
            if duration > db_profiler.slow_query_threshold:
                profiler_logger.warning(
                    f"Slow function: {func.__name__} took {duration:.3f}s"
                )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            profiler_logger.error(
                f"Function {func.__name__} failed after {duration:.3f}s: {e}"
            )
            raise
    
    # Retornar wrapper apropriado baseado no tipo da função
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


@asynccontextmanager
async def profile_session(session: AsyncSession, operation_name: str) -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager para profiling de sessões de banco de dados.
    
    Usage:
        async with profile_session(session, "user_operations") as profiled_session:
            # Usar profiled_session para queries
            result = await profiled_session.execute(query)
    """
    start_time = time.time()
    memory_before = db_profiler._get_memory_usage()
    
    profiler_logger.debug(f"Starting profiled session: {operation_name}")
    
    try:
        yield session
        
        duration = time.time() - start_time
        memory_after = db_profiler._get_memory_usage()
        
        profiler_logger.info(
            f"Session {operation_name} completed in {duration:.3f}s, "
            f"memory delta: {memory_after - memory_before:.2f}MB"
        )
        
        # Registrar métrica de sessão
        REQUEST_LATENCY.labels(
            method=operation_name,
            endpoint='database_session'
        ).observe(duration)
        
    except Exception as e:
        duration = time.time() - start_time
        profiler_logger.error(
            f"Session {operation_name} failed after {duration:.3f}s: {e}"
        )
        raise


async def analyze_slow_queries(threshold_seconds: float = 0.5) -> List[QueryProfile]:
    """
    Analisa queries lentas e retorna relatório detalhado.
    
    Args:
        threshold_seconds: Threshold para considerar uma query lenta
        
    Returns:
        Lista de perfis de queries lentas
    """
    slow_queries = [
        profile for profile in db_profiler.query_profiles
        if profile.duration > threshold_seconds
    ]
    
    # Ordenar por duração (mais lentas primeiro)
    slow_queries.sort(key=lambda q: q.duration, reverse=True)
    
    profiler_logger.info(
        f"Found {len(slow_queries)} slow queries (>{threshold_seconds}s)"
    )
    
    return slow_queries


def get_profiler_stats() -> Dict[str, Any]:
    """
    Retorna estatísticas atuais do profiler.
    
    Returns:
        Dicionário com estatísticas de performance
    """
    report = db_profiler.get_performance_report()
    
    return {
        "enabled": db_profiler.enabled,
        "total_queries": report.total_queries,
        "slow_queries": report.slow_queries,
        "slow_query_percentage": report.slow_query_percentage,
        "avg_duration": report.avg_duration,
        "max_duration": report.max_duration,
        "memory_usage_mb": report.total_memory_usage,
        "cpu_usage_percent": report.avg_cpu_usage,
        "queries_by_table": report.queries_by_table,
        "queries_by_operation": report.queries_by_operation,
        "top_slow_queries": [
            {
                "query": q.query[:200],
                "duration": q.duration,
                "table": q.table,
                "operation": q.operation,
                "memory_delta": q.memory_delta
            }
            for q in report.top_slow_queries[:5]
        ]
    }


__all__ = [
    "DatabaseProfiler",
    "QueryProfile",
    "PerformanceReport",
    "db_profiler",
    "profile_query",
    "profile_session",
    "analyze_slow_queries",
    "get_profiler_stats"
]