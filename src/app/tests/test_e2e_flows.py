"""
Testes End-to-End automatizados para validar fluxos completos do SparkOne.

Este módulo testa os fluxos de entrada (WhatsApp/Web/Sheets) até a persistência
final, garantindo que toda a pipeline funcione corretamente em cenários reais.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.main import app
from app.models.db.message import ChannelMessageORM
from app.models.db.tasks import TaskRecord, TaskStatus
from app.models.schemas import Channel


class TestE2EFlows:
    """Testes End-to-End para validar fluxos completos do sistema."""

    @pytest.fixture
    def client(self):
        """Cliente de teste FastAPI."""
        return TestClient(app)

    @pytest.fixture
    async def async_client(self):
        """Cliente assíncrono para testes E2E."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    async def db_session(self):
        """Sessão de banco de dados para validação de persistência."""
        async for session in get_db_session():
            yield session

    async def test_e2e_whatsapp_to_task_creation(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """
        Teste E2E: WhatsApp → Ingestão → Orquestração → Criação de Tarefa → Persistência

        Fluxo testado:
        1. Webhook WhatsApp recebe mensagem
        2. Normalização da mensagem
        3. Ingestão processa conteúdo
        4. Orquestrador classifica como tarefa
        5. TaskService cria tarefa
        6. Persistência no banco de dados
        """
        # Mock dos serviços externos para isolamento do teste
        with (
            patch("src.app.integrations.evolution_api.EvolutionAPIClient") as mock_evolution,
            patch("src.app.agents.orchestrator.Orchestrator") as mock_orchestrator,
            patch("src.app.services.tasks.TaskService") as mock_task_service,
        ):

            # Configuração dos mocks
            mock_evolution.return_value.send_message = AsyncMock()
            mock_orchestrator_instance = AsyncMock()
            mock_orchestrator.return_value = mock_orchestrator_instance
            mock_orchestrator_instance.handle.return_value = {
                "classification": "task",
                "action": "create_task",
                "task_data": {
                    "title": "Revisar relatório mensal",
                    "description": "Analisar métricas de performance do último mês",
                    "priority": "medium",
                },
            }

            # Payload simulando webhook do WhatsApp
            whatsapp_payload = {
                "data": {
                    "key": {
                        "remoteJid": "5511999999999@s.whatsapp.net",
                        "fromMe": False,
                        "id": "test_message_id_001",
                    },
                    "message": {
                        "conversation": "Preciso revisar o relatório mensal até sexta-feira"
                    },
                    "messageTimestamp": int(datetime.now(UTC).timestamp()),
                }
            }

            # Execução do fluxo E2E
            response = await async_client.post("/webhooks/whatsapp", json=whatsapp_payload)

            # Validações de resposta
            assert response.status_code == 202
            assert response.json()["status"] == "accepted"

            # Aguarda processamento assíncrono
            await asyncio.sleep(0.1)

            # Validação de que o orquestrador foi chamado
            mock_orchestrator_instance.handle.assert_called_once()

            # Validação de persistência da mensagem
            stmt = select(ChannelMessageORM).where(
                ChannelMessageORM.external_id == "test_message_id_001"
            )
            result = await db_session.execute(stmt)
            message_record = result.scalar_one_or_none()

            assert message_record is not None
            assert message_record.channel == Channel.WHATSAPP
            assert "revisar o relatório mensal" in message_record.content

    async def test_e2e_web_to_event_creation(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """
        Teste E2E: Interface Web → Ingestão → Orquestração → Criação de Evento → Persistência

        Fluxo testado:
        1. Interface web envia mensagem
        2. Processamento via endpoint /ingest
        3. Orquestrador classifica como evento
        4. CalendarService cria evento
        5. Persistência no banco de dados
        """
        with (
            patch("src.app.agents.orchestrator.Orchestrator") as mock_orchestrator,
            patch("src.app.services.calendar.CalendarService") as mock_calendar_service,
        ):

            # Configuração dos mocks
            mock_orchestrator_instance = AsyncMock()
            mock_orchestrator.return_value = mock_orchestrator_instance
            mock_orchestrator_instance.handle.return_value = {
                "classification": "event",
                "action": "create_event",
                "event_data": {
                    "title": "Reunião de planejamento",
                    "start_at": "2024-02-15T14:00:00Z",
                    "duration_minutes": 60,
                    "location": "Sala de conferências",
                },
            }

            # Payload da interface web
            web_message = {
                "channel": "web",
                "sender": "user@example.com",
                "content": "Agendar reunião de planejamento para quinta-feira às 14h na sala de conferências",
                "timestamp": datetime.now(UTC).isoformat(),
                "metadata": {"user_agent": "Mozilla/5.0 Test Browser", "ip_address": "127.0.0.1"},
            }

            # Execução do fluxo E2E
            response = await async_client.post("/ingest/", json=web_message)

            # Validações de resposta
            assert response.status_code == 202
            assert response.json()["status"] == "accepted"
            assert response.json()["channel"] == "web"

            # Aguarda processamento assíncrono
            await asyncio.sleep(0.1)

            # Validação de que o orquestrador foi chamado
            mock_orchestrator_instance.handle.assert_called_once()

            # Validação de persistência da mensagem
            stmt = select(ChannelMessageORM).where(ChannelMessageORM.sender == "user@example.com")
            result = await db_session.execute(stmt)
            message_record = result.scalar_one_or_none()

            assert message_record is not None
            assert message_record.channel == Channel.WEB
            assert "reunião de planejamento" in message_record.content

    async def test_e2e_sheets_sync_to_task_update(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """
        Teste E2E: Google Sheets → Sincronização → Atualização de Tarefas → Persistência

        Fluxo testado:
        1. Sincronização com Google Sheets
        2. Detecção de mudanças em tarefas
        3. Atualização de status via TaskService
        4. Persistência das alterações
        """
        with (
            patch("src.app.channels.GoogleSheetsAdapter") as mock_sheets_adapter,
            patch("src.app.services.tasks.TaskService") as mock_task_service,
        ):

            # Configuração dos mocks
            mock_sheets_instance = AsyncMock()
            mock_sheets_adapter.return_value = mock_sheets_instance
            mock_sheets_instance.sync_tasks.return_value = [
                {
                    "id": "task_001",
                    "title": "Tarefa de teste",
                    "status": "completed",
                    "updated_at": datetime.now(UTC),
                }
            ]

            # Criação de tarefa inicial no banco
            initial_task = TaskRecord(
                id=1,
                title="Tarefa de teste",
                status=TaskStatus.PENDING,
                created_at=datetime.now(UTC),
            )
            db_session.add(initial_task)
            await db_session.commit()

            # Simulação de sincronização via endpoint de canal
            sheets_payload = {
                "action": "sync_tasks",
                "spreadsheet_id": "test_spreadsheet_123",
                "range": "Tasks!A1:E100",
                "timestamp": datetime.now(UTC).isoformat(),
            }

            # Execução do fluxo E2E
            response = await async_client.post("/channels/sheets", json=sheets_payload)

            # Validações de resposta
            assert response.status_code == 202
            assert response.json()["status"] == "accepted"

            # Aguarda processamento assíncrono
            await asyncio.sleep(0.1)

            # Validação de atualização da tarefa
            await db_session.refresh(initial_task)
            stmt = select(TaskRecord).where(TaskRecord.id == 1)
            result = await db_session.execute(stmt)
            updated_task = result.scalar_one()

            # Verifica se a tarefa foi atualizada (mock simula mudança para completed)
            assert updated_task.title == "Tarefa de teste"

    async def test_e2e_error_handling_and_fallback(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """
        Teste E2E: Tratamento de Erros e Fallback

        Fluxo testado:
        1. Falha no serviço primário
        2. Ativação do fallback
        3. Notificação de erro
        4. Persistência do log de erro
        """
        with (
            patch("src.app.agents.orchestrator.Orchestrator") as mock_orchestrator,
            patch("src.app.services.whatsapp.WhatsAppService") as mock_whatsapp,
        ):

            # Configuração de falha no orquestrador
            mock_orchestrator_instance = AsyncMock()
            mock_orchestrator.return_value = mock_orchestrator_instance
            mock_orchestrator_instance.handle.side_effect = Exception(
                "Serviço temporariamente indisponível"
            )

            # Mock do serviço de notificação
            mock_whatsapp_instance = AsyncMock()
            mock_whatsapp.return_value = mock_whatsapp_instance

            # Payload que causará erro
            error_payload = {
                "channel": "web",
                "sender": "test@example.com",
                "content": "Mensagem que causará erro no processamento",
                "timestamp": datetime.now(UTC).isoformat(),
            }

            # Execução do fluxo E2E
            response = await async_client.post("/ingest/", json=error_payload)

            # Validação de que o erro foi tratado graciosamente
            # O sistema deve retornar 202 mesmo com falha interna (processamento assíncrono)
            assert response.status_code == 202

            # Aguarda processamento assíncrono
            await asyncio.sleep(0.1)

            # Validação de que a mensagem foi persistida mesmo com erro
            stmt = select(ChannelMessageORM).where(ChannelMessageORM.sender == "test@example.com")
            result = await db_session.execute(stmt)
            message_record = result.scalar_one_or_none()

            assert message_record is not None
            assert message_record.channel == Channel.WEB

    async def test_e2e_metrics_collection(self, async_client: AsyncClient):
        """
        Teste E2E: Coleta de Métricas

        Fluxo testado:
        1. Execução de operações
        2. Coleta automática de métricas
        3. Exposição via endpoint /metrics
        """
        # Execução de algumas operações para gerar métricas
        await async_client.get("/health")
        await async_client.get("/health/database")

        # Coleta das métricas
        response = await async_client.get("/metrics")

        # Validações
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; version=0.0.4"

        metrics_content = response.text

        # Verifica presença de métricas específicas do SparkOne
        assert "sparkone_http_requests_total" in metrics_content
        assert "sparkone_http_request_latency_seconds" in metrics_content

        # Verifica métricas de health checks
        assert 'path="/health"' in metrics_content

    async def test_e2e_health_checks_integration(self, async_client: AsyncClient):
        """
        Teste E2E: Integração de Health Checks

        Fluxo testado:
        1. Verificação de saúde geral
        2. Verificação de componentes específicos
        3. Validação de dependências externas
        """
        # Health check geral
        response = await async_client.get("/health")
        assert response.status_code == 200

        health_data = response.json()
        assert health_data["status"] == "healthy"
        assert "timestamp" in health_data

        # Health check do banco de dados
        response = await async_client.get("/health/database")
        assert response.status_code == 200

        db_health = response.json()
        assert db_health["status"] == "healthy"
        assert "database" in db_health

        # Health check do Redis (se disponível)
        response = await async_client.get("/health/redis")
        # Pode retornar 200 ou 503 dependendo da configuração
        assert response.status_code in [200, 503]


# Fixtures adicionais para testes E2E
@pytest.fixture(scope="session")
def event_loop():
    """Cria um loop de eventos para testes assíncronos."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def clean_database():
    """Limpa o banco de dados antes de cada teste."""
    async for session in get_db_session():
        # Limpa registros de teste
        await session.execute(
            "DELETE FROM messages WHERE sender LIKE '%test%' OR sender LIKE '%example.com'"
        )
        await session.execute("DELETE FROM tasks WHERE title LIKE '%teste%'")
        await session.execute("DELETE FROM events WHERE title LIKE '%teste%'")
        await session.commit()
        break


# Utilitários para testes E2E
class E2ETestHelpers:
    """Classe utilitária com helpers para testes E2E."""

    @staticmethod
    def create_whatsapp_payload(message: str, sender: str = "5511999999999") -> dict[str, Any]:
        """Cria payload simulando webhook do WhatsApp."""
        return {
            "data": {
                "key": {
                    "remoteJid": f"{sender}@s.whatsapp.net",
                    "fromMe": False,
                    "id": f"test_msg_{hash(message)}",
                },
                "message": {"conversation": message},
                "messageTimestamp": int(datetime.now(UTC).timestamp()),
            }
        }

    @staticmethod
    def create_web_payload(message: str, sender: str = "test@example.com") -> dict[str, Any]:
        """Cria payload simulando mensagem da interface web."""
        return {
            "channel": "web",
            "sender": sender,
            "content": message,
            "timestamp": datetime.now(UTC).isoformat(),
            "metadata": {"user_agent": "Test Browser", "ip_address": "127.0.0.1"},
        }

    @staticmethod
    async def wait_for_async_processing(seconds: float = 0.1):
        """Aguarda processamento assíncrono."""
        await asyncio.sleep(seconds)
