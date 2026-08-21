from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    jobpilot_env: str = "development"
    jobpilot_config: str = "config/jobpilot.yaml"
    database_url: str = "sqlite+pysqlite:///./jobpilot.db"
    redis_url: str = "redis://localhost:6379/0"
    jobpilot_allow_live_apply: bool = False

    llm_provider: str = "heuristic"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    email_provider: str = "smtp"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    email_from: str = ""
    email_to: str = ""

    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    github_token: str = ""
    github_username: str = "Dna072"
    http_user_agent: str = "JobPilot/0.1 (+https://github.com/Dna072/jobpilot)"

    port: int = 8080
    jobpilot_ops_token: str = ""
    gcs_bucket: str = ""
    gcs_prefix: str = "jobpilot"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@lru_cache
def load_app_config(config_path: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    path = Path(config_path or settings.jobpilot_config)
    if not path.is_absolute():
        path = ROOT / path
    return load_yaml(path)


def repo_path(*parts: str) -> Path:
    return ROOT.joinpath(*parts)
