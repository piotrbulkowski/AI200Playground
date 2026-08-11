"""Pydantic-settings configuration, one profile per deployment target.

`development` and `azure` both point at the same real Azure Storage account today (Phase 1
has no separate deployed compute target yet) — the concrete difference is that `azure` reads
only real process env vars while `development`/`test` also load a local `.env` file. This will
grow more meaningful once Phases 7-8 add real deployment and App Configuration/Key Vault.
"""

from __future__ import annotations

import os
from enum import StrEnum
from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_DEFAULT_ALLOWED_CONTENT_TYPES = [
    "application/pdf",
    "text/plain",
    "text/markdown",
    "application/json",
]


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    AZURE = "azure"


class Settings(BaseSettings):
    environment: Environment = Environment.DEVELOPMENT

    # Azure Storage — auth is always DefaultAzureCredential, never a key/connection string.
    azure_storage_account_url: str
    azure_storage_container: str = "documents"

    # Postgres — local Docker Compose instance in all profiles for now.
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "ai200_dev"
    postgres_user: str = "ai200"
    postgres_password: str
    postgres_pool_min_size: int = 1
    postgres_pool_max_size: int = 10

    upload_max_size_mb: int = 50
    allowed_content_types: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: list(_DEFAULT_ALLOWED_CONTENT_TYPES)
    )

    @field_validator("allowed_content_types", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class DevelopmentSettings(Settings):
    pass


class TestSettings(Settings):
    azure_storage_container: str = "documents-test"
    postgres_db: str = "ai200_test"


class AzureSettings(Settings):
    # No .env file here — a deployed environment supplies real process env vars only.
    model_config = SettingsConfigDict(extra="ignore")


_SETTINGS_BY_ENVIRONMENT: dict[str, type[Settings]] = {
    Environment.DEVELOPMENT.value: DevelopmentSettings,
    Environment.TEST.value: TestSettings,
    Environment.AZURE.value: AzureSettings,
}


@lru_cache
def get_settings() -> Settings:
    environment = os.environ.get("ENVIRONMENT", Environment.DEVELOPMENT.value)
    settings_cls = _SETTINGS_BY_ENVIRONMENT.get(environment, DevelopmentSettings)
    return settings_cls()
