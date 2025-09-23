"""Utility script to prepare local development environment."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UPLOAD_DIR = ROOT / os.getenv("WEB_UPLOAD_DIR", "uploads")
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"


def ensure_upload_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✔ Upload directory ready: {UPLOAD_DIR}")


def ensure_env_file() -> None:
    if ENV_FILE.exists():
        print("✔ .env already present, skipping copy")
        return
    if not ENV_EXAMPLE.exists():
        print("⚠️  .env.example not found; skipping copy")
        return
    shutil.copy(ENV_EXAMPLE, ENV_FILE)
    print("✔ Created .env from .env.example")


def main() -> None:
    ensure_upload_dir()
    ensure_env_file()
    print("Bootstrap completed. Run `make install-dev` next.")


if __name__ == "__main__":
    main()
