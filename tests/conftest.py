from __future__ import annotations

import os

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JOBPILOT_ALLOW_LIVE_APPLY", "false")
os.environ.setdefault("LLM_PROVIDER", "heuristic")
os.environ.setdefault("JOBPILOT_CONFIG", "config/jobpilot.yaml")

from jobpilot.config import get_settings, load_app_config
from jobpilot.db.models import init_db, reset_engine


@pytest.fixture(autouse=True)
def _db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{tmp_path}/test.db")
    get_settings.cache_clear()
    load_app_config.cache_clear()
    reset_engine()
    init_db()
    yield
    reset_engine()
    get_settings.cache_clear()
