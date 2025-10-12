"""SparkOne application package.

This module also exposes compatibility aliases so tests that refer to
"src.app.*" module paths can patch the same modules imported as "app.*".
"""

from __future__ import annotations

import importlib
import sys
import types


# Create a lightweight alias so that importing/patching "src.app.*" in tests
# refers to the same modules loaded under the canonical "app.*" package.
try:
    # Ensure a top-level placeholder module for "src"
    src_pkg = sys.modules.setdefault("src", types.ModuleType("src"))
    # Alias the current package ("app") under "src.app"
    sys.modules.setdefault("src.app", sys.modules[__name__])

    # Proactively alias common subpackages used in tests
    for subpath in (
        "routers.alerts",
        "routers.webhooks",
        "routers.health",
        "channels",
        "middleware.security_logging",
        "middleware.rate_limiting",
        "agents.orchestrator",
        "services.ingestion",
        "services.tasks",
        "services.whatsapp",
        "integrations.evolution_api",
        "workers.scheduler",
    ):
        try:
            mod = importlib.import_module(f"app.{subpath}")
            sys.modules[f"src.app.{subpath}"] = mod
        except Exception:
            # Best-effort aliasing; ignore modules that fail to import during init
            pass
except Exception:
    # Alias setup is best-effort and should never break runtime
    pass
