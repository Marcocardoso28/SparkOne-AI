from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from app.config import get_settings

UPLOAD_DIR = Path("uploads")


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    get_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _ensure_upload_dir(tmp_path_factory: pytest.TempPathFactory):
    tmp_uploads = tmp_path_factory.mktemp("uploads")
    os.environ.setdefault("WEB_UPLOAD_DIR", str(tmp_uploads))
    yield
    shutil.rmtree(tmp_uploads, ignore_errors=True)
    os.environ.pop("WEB_UPLOAD_DIR", None)
