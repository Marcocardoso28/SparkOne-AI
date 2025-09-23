"""Utility helpers for parsing structured responses."""

from __future__ import annotations

import json
from typing import Any


def safe_json_loads(payload: str) -> dict[str, Any]:
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return {"raw": payload}


__all__ = ["safe_json_loads"]
