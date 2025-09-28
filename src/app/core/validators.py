"""
Validadores robustos para entrada de dados nos endpoints críticos da API.
Implementa validações de segurança, sanitização e controle de tamanho.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)

# Constantes para validação
MAX_MESSAGE_LENGTH = 10000
MAX_SENDER_LENGTH = 100
MAX_CHANNEL_LENGTH = 50
MAX_EXTRA_DATA_SIZE = 5000
MAX_EXTRA_DATA_KEYS = 20
MAX_STRING_FIELD_LENGTH = 1000
MAX_PAYLOAD_SIZE = 10000
MAX_QUERY_PARAM_LENGTH = 500
MAX_USERNAME_LENGTH = 50
MAX_PASSWORD_LENGTH = 100

# Tipos de conteúdo permitidos
ALLOWED_CONTENT_TYPES = {
    "text/plain",
    "application/json",
    "multipart/form-data",
    "application/x-www-form-urlencoded",
}

# Padrões para detectar tentativas de XSS e SQL Injection
XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe[^>]*>",
    r"<object[^>]*>",
    r"<embed[^>]*>",
    r"<link[^>]*>",
    r"<meta[^>]*>",
    r"<style[^>]*>.*?</style>",
    r"expression\s*\(",
    r"url\s*\(",
    r"@import",
    r"vbscript:",
    r"data:text/html",
]

SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
    r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
    r"(\b(OR|AND)\s+['\"']?\w+['\"']?\s*=\s*['\"']?\w+['\"']?)",
    r"(--|#|/\*|\*/)",
    r"(\bxp_\w+)",
    r"(\bsp_\w+)",
    r"(\bEXEC\s*\()",
    r"(\bCAST\s*\()",
    r"(\bCONVERT\s*\()",
    r"(\bCHAR\s*\()",
    r"(\bASCII\s*\()",
    r"(\bSUBSTRING\s*\()",
    r"(\bLEN\s*\()",
    r"(\bLENGTH\s*\()",
    r"(\bCOUNT\s*\()",
    r"(\bSUM\s*\()",
    r"(\bAVG\s*\()",
    r"(\bMIN\s*\()",
    r"(\bMAX\s*\()",
    r"(\bGROUP\s+BY)",
    r"(\bORDER\s+BY)",
    r"(\bHAVING\b)",
    r"(\bLIMIT\b)",
    r"(\bOFFSET\b)",
    r"(\bINTO\s+OUTFILE)",
    r"(\bLOAD_FILE\s*\()",
    r"(\bINTO\s+DUMPFILE)",
    r"(\bSLEEP\s*\()",
    r"(\bBENCHMARK\s*\()",
    r"(\bEXTRACTVALUE\s*\()",
    r"(\bUPDATEXML\s*\()",
    r"(\bGETLOCK\s*\()",
    r"(\bRELEASE_LOCK\s*\()",
    r"(\bIS_FREE_LOCK\s*\()",
    r"(\bIS_USED_LOCK\s*\()",
    r"(\bMASTER_POS_WAIT\s*\()",
    r"(\bNAME_CONST\s*\()",
    r"(\bVERSION\s*\()",
    r"(\b@@\w+)",
    r"(\bINFORMATION_SCHEMA\b)",
    r"(\bSYS\.\w+)",
    r"(\bMYSQL\.\w+)",
    r"(\bPERFORMANCE_SCHEMA\b)",
]

# Padrões para detectar tentativas de Path Traversal
PATH_TRAVERSAL_PATTERNS = [
    r"\.\./",
    r"\.\.\\",
    r"%2e%2e%2f",
    r"%2e%2e%5c",
    r"..%2f",
    r"..%5c",
    r"%252e%252e%252f",
    r"%252e%252e%255c",
]

# Combinação de todos os padrões perigosos
DANGEROUS_PATTERNS = XSS_PATTERNS + SQL_INJECTION_PATTERNS + PATH_TRAVERSAL_PATTERNS

# Magic bytes para validação de arquivos
ALLOWED_FILE_SIGNATURES = {
    # Imagens
    b"\xFF\xD8\xFF": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"RIFF\x00\x00\x00\x00WEBP": "image/webp",  # WebP específico
    b"BM": "image/bmp",
    # Áudio
    b"ID3": "audio/mpeg",
    b"\xFF\xFB": "audio/mpeg",
    b"\xFF\xF3": "audio/mpeg",
    b"\xFF\xF2": "audio/mpeg",
    b"RIFF\x00\x00\x00\x00WAVE": "audio/wav",  # WAV específico
    b"fLaC": "audio/flac",
    b"OggS": "audio/ogg",
    # Documentos
    b"%PDF": "application/pdf",
    b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1": "application/msword",
    b"PK\x03\x04": "application/zip",  # Também usado por docx, xlsx, etc.
}


class SecureChannelMessage(BaseModel):
    """Modelo com validação robusta para mensagens de canal."""

    channel: str = Field(..., min_length=1, max_length=50)
    sender: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH)
    message_type: str = Field(default="free_text", max_length=50)
    extra_data: dict[str, Any] = Field(default_factory=dict)

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v: str) -> str:
        """Valida e sanitiza o nome do canal."""
        if not v or not isinstance(v, str):
            raise ValueError("Canal deve ser uma string não vazia")

        # Permitir apenas caracteres alfanuméricos e underscore
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Canal deve conter apenas letras, números e underscore")

        return v.lower().strip()

    @field_validator("sender")
    @classmethod
    def validate_sender(cls, v: str) -> str:
        """Valida e sanitiza o identificador do remetente."""
        if not v or not isinstance(v, str):
            raise ValueError("Remetente deve ser uma string não vazia")

        # Sanitizar caracteres perigosos
        sanitized = sanitize_string(v)
        if len(sanitized) < 1:
            raise ValueError("Remetente não pode estar vazio após sanitização")

        return sanitized

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Valida e sanitiza o conteúdo da mensagem."""
        if not v or not isinstance(v, str):
            raise ValueError("Conteúdo deve ser uma string não vazia")

        # Verificar padrões perigosos
        if contains_dangerous_patterns(v):
            logger.warning(f"Conteúdo bloqueado por conter padrões perigosos: {v[:100]}...")
            raise ValueError("Conteúdo contém padrões não permitidos")

        # Sanitizar e validar tamanho
        sanitized = sanitize_string(v)
        if len(sanitized) > MAX_MESSAGE_LENGTH:
            raise ValueError(f"Conteúdo muito longo. Máximo: {MAX_MESSAGE_LENGTH} caracteres")

        return sanitized

    @field_validator("message_type")
    @classmethod
    def validate_message_type(cls, v: str) -> str:
        """Valida o tipo de mensagem."""
        allowed_types = {"free_text", "task", "event", "coaching", "unknown"}
        if v not in allowed_types:
            raise ValueError(f"Tipo de mensagem deve ser um de: {', '.join(allowed_types)}")
        return v

    @field_validator("extra_data")
    @classmethod
    def validate_extra_data(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Valida dados extras."""
        if not isinstance(v, dict):
            raise ValueError("extra_data deve ser um dicionário")

        if len(v) > MAX_EXTRA_DATA_KEYS:
            raise ValueError(f"Muitas chaves em extra_data. Máximo: {MAX_EXTRA_DATA_KEYS}")

        # Validar chaves e valores
        sanitized = {}
        for key, value in v.items():
            if not isinstance(key, str) or len(key) > 100:
                raise ValueError("Chaves de extra_data devem ser strings de até 100 caracteres")

            # Sanitizar chave
            clean_key = sanitize_string(key)
            if not clean_key:
                continue

            # Validar valor baseado no tipo
            if isinstance(value, str):
                if len(value) > MAX_STRING_FIELD_LENGTH:
                    raise ValueError(
                        f"Valor string muito longo para chave '{key}'. "
                        f"Máximo: {MAX_STRING_FIELD_LENGTH}"
                    )
                sanitized[clean_key] = sanitize_string(value)
            elif isinstance(value, int | float | bool):
                sanitized[clean_key] = value
            elif value is None:
                sanitized[clean_key] = None
            else:
                # Converter outros tipos para string e sanitizar
                str_value = str(value)
                if len(str_value) > MAX_STRING_FIELD_LENGTH:
                    raise ValueError(
                        f"Valor muito longo para chave '{key}'. Máximo: {MAX_STRING_FIELD_LENGTH}"
                    )
                sanitized[clean_key] = sanitize_string(str_value)

        return sanitized


class SecureWebhookPayload(BaseModel):
    """Modelo com validação robusta para payloads de webhook."""

    payload: dict[str, Any]

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: Any) -> dict[str, Any]:
        """Aceita payload bruto ou embrulhado em uma chave interna."""

        if not isinstance(value, dict):
            raise ValueError("Payload deve ser um dicionário")

        candidate = value.get("payload", value)
        if not isinstance(candidate, dict):
            raise ValueError("Payload deve ser um dicionário")

        payload_str = str(candidate)
        if len(payload_str) > MAX_PAYLOAD_SIZE:
            raise ValueError(f"Payload muito grande. Máximo: {MAX_PAYLOAD_SIZE} bytes")

        sanitized = sanitize_dict(candidate)
        return {"payload": sanitized}


class SecureQueryParams(BaseModel):
    """Validador para parâmetros de query seguros."""
    
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    threshold: float | None = Field(default=None, ge=0.0, le=10.0)

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v: int) -> int:
        if v > 100:
            raise ValueError("Limite muito alto")
        return v

    @field_validator("offset")
    @classmethod
    def validate_offset(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Offset deve ser positivo")
        return v


class SecureLoginCredentials(BaseModel):
    """Validador para credenciais de login seguras."""
    
    username: str = Field(..., min_length=3, max_length=MAX_USERNAME_LENGTH)
    password: str = Field(..., min_length=8, max_length=MAX_PASSWORD_LENGTH)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Valida o nome de usuário."""
        if contains_dangerous_patterns(v):
            raise ValueError("Nome de usuário contém padrões perigosos")
        
        sanitized = sanitize_string(v)
        if len(sanitized.strip()) < 3:
            raise ValueError("Nome de usuário muito curto após sanitização")
        
        return sanitized

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Valida a senha com critérios de segurança."""
        if len(v) < 8:
            raise ValueError("Senha muito fraca")
        
        # Verificar se tem pelo menos uma letra maiúscula, minúscula, número e símbolo
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_symbol = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not (has_upper and has_lower and has_digit and has_symbol):
            raise ValueError("Senha muito fraca")
        
        if contains_dangerous_patterns(v):
            raise ValueError("Senha contém padrões perigosos")
        
        return v


def sanitize_string(value: str) -> str:
    """
    Sanitiza uma string removendo caracteres perigosos.

    Args:
        value: String a ser sanitizada

    Returns:
        String sanitizada
    """
    if not isinstance(value, str):
        return str(value)

    # Remover caracteres de controle (exceto \n, \r, \t)
    sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", value)

    # Remover padrões perigosos
    for pattern in DANGEROUS_PATTERNS:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

    # Limitar tamanho
    if len(sanitized) > MAX_STRING_FIELD_LENGTH:
        sanitized = sanitized[:MAX_STRING_FIELD_LENGTH]

    return sanitized.strip()


def sanitize_dict(data: dict[str, Any], max_depth: int = 5) -> dict[str, Any]:
    """
    Sanitiza recursivamente um dicionário.

    Args:
        data: Dicionário a ser sanitizado
        max_depth: Profundidade máxima de recursão

    Returns:
        Dicionário sanitizado
    """
    if max_depth <= 0:
        return {}

    if not isinstance(data, dict):
        return {}

    sanitized = {}
    for key, value in data.items():
        if not isinstance(key, str) or len(key) > 100:
            continue

        clean_key = sanitize_string(key)
        if not clean_key:
            continue

        if isinstance(value, str):
            sanitized[clean_key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[clean_key] = sanitize_dict(value, max_depth - 1)
        elif isinstance(value, list):
            sanitized[clean_key] = sanitize_list(value, max_depth - 1)
        elif isinstance(value, int | float | bool) or value is None:
            sanitized[clean_key] = value
        else:
            # Converter para string e sanitizar
            sanitized[clean_key] = sanitize_string(str(value))

    return sanitized


def sanitize_list(data: list[Any], max_depth: int = 5) -> list[Any]:
    """
    Sanitiza recursivamente uma lista.

    Args:
        data: Lista a ser sanitizada
        max_depth: Profundidade máxima de recursão

    Returns:
        Lista sanitizada
    """
    if max_depth <= 0 or not isinstance(data, list):
        return []

    sanitized = []
    for item in data[:100]:  # Limitar tamanho da lista
        if isinstance(item, str):
            sanitized.append(sanitize_string(item))
        elif isinstance(item, dict):
            sanitized.append(sanitize_dict(item, max_depth - 1))
        elif isinstance(item, list):
            sanitized.append(sanitize_list(item, max_depth - 1))
        elif isinstance(item, int | float | bool) or item is None:
            sanitized.append(item)
        else:
            sanitized.append(sanitize_string(str(item)))

    return sanitized


def contains_dangerous_patterns(text: str) -> bool:
    """
    Verifica se o texto contém padrões perigosos.

    Args:
        text: Texto a ser verificado

    Returns:
        True se contém padrões perigosos
    """
    if not isinstance(text, str):
        return False

    # Verificar padrões XSS
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    # Verificar padrões de SQL injection
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


def validate_file_upload(
    file_content: bytes, content_type: str, max_size: int = 10 * 1024 * 1024
) -> None:
    """
    Valida upload de arquivo.

    Args:
        file_content: Conteúdo do arquivo
        content_type: Tipo MIME do arquivo
        max_size: Tamanho máximo permitido em bytes

    Raises:
        HTTPException: Se a validação falhar
    """
    if not file_content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo vazio")

    if len(file_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo muito grande. Máximo: {max_size} bytes",
        )

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de arquivo não permitido. Permitidos: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )

    # Verificar magic bytes para validação adicional
    if not _validate_file_magic_bytes(file_content, content_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo não corresponde ao tipo declarado",
        )


def _validate_file_magic_bytes(content: bytes, content_type: str) -> bool:
    """
    Valida magic bytes do arquivo.

    Args:
        content: Conteúdo do arquivo
        content_type: Tipo MIME declarado

    Returns:
        True se os magic bytes correspondem ao tipo
    """
    if len(content) < 4:
        return False

    magic_bytes = content[:4]

    # Magic bytes para tipos de arquivo comuns
    magic_signatures = {
        "image/jpeg": [b"\xFF\xD8\xFF"],
        "image/png": [b"\x89PNG"],
        "image/gif": [b"GIF8"],
        "image/webp": [b"RIFF"],
        "audio/mpeg": [b"ID3", b"\xFF\xFB", b"\xFF\xF3", b"\xFF\xF2"],
        "audio/wav": [b"RIFF"],
        "audio/ogg": [b"OggS"],
    }

    expected_signatures = magic_signatures.get(content_type, [])
    if not expected_signatures:
        return True  # Tipo não verificável, permitir

    for signature in expected_signatures:
        if magic_bytes.startswith(signature):
            return True

    return False


def detect_dangerous_patterns(text: str) -> list[str]:
    """
    Detecta padrões perigosos no texto fornecido.
    
    Args:
        text: Texto a ser analisado
        
    Returns:
        Lista de padrões perigosos encontrados
    """
    found_patterns = []
    
    # Verifica XSS
    for pattern in XSS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            found_patterns.append(f"XSS: {pattern}")
    
    # Verifica SQL Injection
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            found_patterns.append(f"SQL Injection: {pattern}")
    
    # Verifica Path Traversal
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            found_patterns.append(f"Path Traversal: {pattern}")
    
    return found_patterns


__all__ = [
    "SecureChannelMessage",
    "SecureWebhookPayload", 
    "SecureQueryParams",
    "SecureLoginCredentials",
    "sanitize_string",
    "sanitize_dict",
    "contains_dangerous_patterns",
    "detect_dangerous_patterns",
    "validate_file_upload",
]
