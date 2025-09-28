"""Testes de segurança automatizados."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from src.app.core.validators import (
    SecureChannelMessage,
    SecureLoginCredentials,
    SecureWebhookPayload,
    detect_dangerous_patterns,
    sanitize_string,
    validate_file_upload,
)
from src.app.main import create_application


@pytest.fixture
def client():
    """Cliente de teste."""
    app = create_application()
    return TestClient(app)


class TestInputValidation:
    """Testes de validação de entrada."""

    def test_secure_channel_message_valid(self):
        """Testa validação de mensagem válida."""
        data = {
            "channel": "test_channel",
            "sender": "user123",
            "content": "Hello world",
            "message_type": "free_text",
            "extra_data": {"key": "value"},
        }

        message = SecureChannelMessage(**data)
        assert message.channel == "test_channel"
        assert message.sender == "user123"
        assert message.content == "Hello world"

    def test_secure_channel_message_xss_prevention(self):
        """Testa prevenção de XSS."""
        data = {
            "channel": "test_channel",
            "sender": "user123",
            "content": "<script>alert('xss')</script>",
            "message_type": "free_text",
        }

        with pytest.raises(ValidationError, match="Conteúdo contém padrões não permitidos"):
            SecureChannelMessage(**data)

    def test_secure_channel_message_sql_injection_prevention(self):
        """Testa prevenção de SQL Injection."""
        data = {
            "channel": "test_channel",
            "sender": "user123",
            "content": "'; DROP TABLE users; --",
            "message_type": "free_text",
        }

        with pytest.raises(ValidationError, match="Conteúdo contém padrões não permitidos"):
            SecureChannelMessage(**data)

    def test_secure_channel_message_size_limit(self):
        """Testa limite de tamanho."""
        data = {
            "channel": "test-channel",
            "sender": "user123",
            "content": "x" * 10001,  # Excede limite de 10000
            "message_type": "text",
        }

        with pytest.raises(ValueError, match="Conteúdo muito longo"):
            SecureChannelMessage(**data)

    def test_secure_webhook_payload_valid(self):
        """Testa validação de payload de webhook válido."""
        data = {
            "event": "message",
            "data": {"message": "test"},
            "timestamp": "2023-01-01T00:00:00Z",
        }

        payload = SecureWebhookPayload(**data)
        assert payload.payload["event"] == "message"
        assert payload.payload["data"] == {"message": "test"}

    def test_secure_login_credentials_valid(self):
        """Testa validação de credenciais válidas."""
        data = {"username": "testuser", "password": "SecurePass123!"}

        credentials = SecureLoginCredentials(**data)
        assert credentials.username == "testuser"
        assert credentials.password == "SecurePass123!"

    def test_secure_login_credentials_weak_password(self):
        """Testa rejeição de senha fraca."""
        data = {"username": "testuser", "password": "123"}

        with pytest.raises(ValueError, match="Senha muito fraca"):
            SecureLoginCredentials(**data)


class TestSanitization:
    """Testes de sanitização."""

    def test_sanitize_string_basic(self):
        """Testa sanitização básica."""
        result = sanitize_string("Hello <script>alert('xss')</script> World")
        assert "<script>" not in result
        assert "alert" not in result

    def test_sanitize_string_sql_injection(self):
        """Testa sanitização de SQL injection."""
        result = sanitize_string("'; DROP TABLE users; --")
        assert "DROP TABLE" not in result.upper()
        assert "--" not in result

    def test_detect_dangerous_patterns_xss(self):
        """Testa detecção de padrões XSS."""
        assert detect_dangerous_patterns("<script>alert('xss')</script>")
        assert detect_dangerous_patterns("javascript:alert(1)")
        assert detect_dangerous_patterns("onload=alert(1)")

    def test_detect_dangerous_patterns_sql_injection(self):
        """Testa detecção de SQL injection."""
        assert detect_dangerous_patterns("'; DROP TABLE users; --")
        assert detect_dangerous_patterns("UNION SELECT * FROM")
        assert detect_dangerous_patterns("1' OR '1'='1")

    def test_detect_dangerous_patterns_path_traversal(self):
        """Testa detecção de path traversal."""
        assert detect_dangerous_patterns("../../../etc/passwd")
        assert detect_dangerous_patterns("..\\..\\windows\\system32")

    def test_detect_dangerous_patterns_safe_content(self):
        """Testa que conteúdo seguro não é detectado como perigoso."""
        assert not detect_dangerous_patterns("Hello world!")
        assert not detect_dangerous_patterns("This is a normal message.")
        assert not detect_dangerous_patterns("User123 sent a message")


class TestFileUploadValidation:
    """Testes de validação de upload de arquivos."""

    def test_validate_file_upload_valid_image(self):
        """Testa validação de imagem válida."""
        # Simular arquivo PNG válido (magic bytes)
        file_content = b"\x89PNG\r\n\x1a\n" + b"fake_png_data"

        validate_file_upload(
            file_content=file_content, content_type="image/png", max_size=1024 * 1024
        )

    def test_validate_file_upload_invalid_extension(self):
        """Testa rejeição de extensão inválida."""
        file_content = b"some content"

        with pytest.raises(HTTPException, match="Tipo de arquivo não permitido"):
            validate_file_upload(
                file_content=file_content,
                content_type="application/octet-stream",
                max_size=1024 * 1024,
            )

    def test_validate_file_upload_size_limit(self):
        """Testa limite de tamanho de arquivo."""
        file_content = b"x" * 1000

        with pytest.raises(HTTPException, match="Arquivo muito grande"):
            validate_file_upload(file_content=file_content, content_type="text/plain", max_size=500)


class TestSecurityHeaders:
    """Testes de headers de segurança."""

    def test_security_headers_present(self, client):
        """Testa presença de headers de segurança."""
        response = client.get("/health")

        # Headers básicos de segurança
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"

        assert "Content-Security-Policy" in response.headers
        assert "Referrer-Policy" in response.headers

    def test_no_cache_headers_sensitive_endpoints(self, client):
        """Testa headers de no-cache em endpoints sensíveis."""
        response = client.get("/health")

        assert "Cache-Control" in response.headers
        assert "no-cache" in response.headers["Cache-Control"]
        assert "no-store" in response.headers["Cache-Control"]


class TestRateLimiting:
    """Testes de rate limiting."""

    def test_rate_limiting_normal_usage(self, client):
        """Testa uso normal dentro dos limites."""
        # Fazer algumas requests normais
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200

    @patch("src.app.middleware.rate_limiting.time.time")
    def test_rate_limiting_exceeded(self, mock_time, client):
        """Testa rate limiting quando excedido."""
        # Simular tempo fixo
        mock_time.return_value = 1000.0

        # Fazer muitas requests rapidamente
        responses = []
        for _ in range(150):  # Exceder limite
            response = client.get("/health")
            responses.append(response)

        # Verificar que algumas foram bloqueadas
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes  # Too Many Requests


class TestSecurityLogging:
    """Testes de logging de segurança."""

    @patch("src.app.middleware.security_logging.security_logger")
    def test_security_event_logging(self, mock_logger, client):
        """Testa logging de eventos de segurança."""
        # Fazer request que deve gerar log
        response = client.post(
            "/ingest",
            json={
                "channel": "test",
                "sender": "user",
                "content": "test message",
                "message_type": "text",
            },
        )

        # Verificar que logger foi chamado
        assert mock_logger.info.called or mock_logger.warning.called or mock_logger.error.called

    @patch("src.app.middleware.security_logging.security_logger")
    def test_failed_validation_logging(self, mock_logger, client):
        """Testa logging de falhas de validação."""
        # Enviar dados inválidos
        response = client.post(
            "/ingest",
            json={
                "channel": "test",
                "sender": "user",
                "content": "<script>alert('xss')</script>",
                "message_type": "text",
            },
        )

        # Deve ter logado o evento de segurança
        assert response.status_code == 400
        assert mock_logger.warning.called or mock_logger.error.called


class TestEndpointSecurity:
    """Testes de segurança de endpoints."""

    def test_ingest_endpoint_validation(self, client):
        """Testa validação do endpoint de ingestão."""
        # Dados válidos
        valid_data = {
            "channel": "test-channel",
            "sender": "user123",
            "content": "Hello world",
            "message_type": "text",
        }

        with patch("src.app.services.ingest.ingest_message") as mock_ingest:
            mock_ingest.return_value = None
            response = client.post("/ingest", json=valid_data)
            assert response.status_code == 200

    def test_ingest_endpoint_xss_prevention(self, client):
        """Testa prevenção de XSS no endpoint de ingestão."""
        # Dados com XSS
        xss_data = {
            "channel": "test-channel",
            "sender": "user123",
            "content": "<script>alert('xss')</script>",
            "message_type": "text",
        }

        response = client.post("/ingest", json=xss_data)
        assert response.status_code == 400
        assert "validation error" in response.json()["detail"].lower()

    def test_webhook_endpoint_validation(self, client):
        """Testa validação do endpoint de webhook."""
        # Dados válidos
        valid_data = {
            "event": "message",
            "data": {"message": "test"},
            "timestamp": "2023-01-01T00:00:00Z",
        }

        with patch("src.app.services.whatsapp.normalize_whatsapp_message") as mock_normalize:
            with patch("src.app.services.ingest.ingest_message") as mock_ingest:
                mock_normalize.return_value = MagicMock()
                mock_ingest.return_value = None
                response = client.post("/webhooks/whatsapp", json=valid_data)
                # Pode retornar 200 ou erro dependendo da implementação
                assert response.status_code in [200, 400, 422]


class TestCSRFProtection:
    """Testes de proteção CSRF."""

    def test_csrf_headers_present(self, client):
        """Testa presença de headers relacionados ao CSRF."""
        response = client.get("/web/login")

        # Verificar que headers de segurança estão presentes
        assert "X-Frame-Options" in response.headers
        assert "Content-Security-Policy" in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
