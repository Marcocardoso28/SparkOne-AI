"""Worker package exports for easier monkeypatching in tests."""

from __future__ import annotations

# Ensure submodules are accessible as attributes for dotted imports in tests
from . import scheduler as scheduler  # noqa: F401
