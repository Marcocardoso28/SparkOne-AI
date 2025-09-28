"""Utility helpers for parsing structured responses."""

from __future__ import annotations

import json
from typing import Any


def safe_json_loads(payload: str) -> dict[str, Any]:
    """Parse JSON from LLM response, handling markdown code blocks."""

    # Primeiro tenta o payload direto
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        pass

    # Se falhar, tenta extrair JSON de bloco markdown
    import re

    # Procura por blocos ```json ou ```
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', payload, re.DOTALL)
    if json_match:
        json_content = json_match.group(1).strip()
        try:
            return json.loads(json_content)
        except json.JSONDecodeError:
            pass

    # Se ainda falhar, procura por qualquer estrutura que pareça JSON
    json_match = re.search(r'\{.*\}', payload, re.DOTALL)
    if json_match:
        json_content = json_match.group(0).strip()
        try:
            return json.loads(json_content)
        except json.JSONDecodeError:
            pass

    # Como último recurso, retorna o payload raw
    return {"raw": payload}


__all__ = ["safe_json_loads"]
