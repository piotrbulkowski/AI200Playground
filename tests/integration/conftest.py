"""Fixtures for integration tests. These hit the real Postgres (Docker Compose) and, once
provisioned, the real Azure Storage account — never mocks of the SDKs."""

from __future__ import annotations

import os

import pytest
import pytest_asyncio

os.environ.setdefault("ENVIRONMENT", "test")

from src.config import get_settings  # noqa: E402
from src.infrastructure.postgres.migrations import run_migrations  # noqa: E402
from src.infrastructure.postgres.pool import close_pool, create_pool  # noqa: E402


@pytest.fixture(scope="session")
def settings():
    return get_settings()


@pytest_asyncio.fixture
async def pg_pool(settings):
    pool = await create_pool(
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
        min_size=settings.postgres_pool_min_size,
        max_size=settings.postgres_pool_max_size,
    )
    await run_migrations(pool)
    async with pool.acquire() as conn:
        await conn.execute("TRUNCATE TABLE documents")
    try:
        yield pool
    finally:
        await close_pool(pool)
