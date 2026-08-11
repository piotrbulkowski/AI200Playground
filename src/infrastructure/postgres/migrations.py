"""Bespoke, dependency-free SQL migration runner.

Numbered files in migrations_sql/ are applied in order and tracked in a
schema_migrations table. No Alembic/SQLAlchemy — Phase 3 will add pgvector-specific
DDL that an ORM migration tool would only get in the way of.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import asyncpg

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).parent / "migrations_sql"

_CREATE_TRACKING_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


async def run_migrations(pool: asyncpg.Pool) -> list[str]:
    applied: list[str] = []
    async with pool.acquire() as conn:
        await conn.execute(_CREATE_TRACKING_TABLE)
        already_applied = {
            row["version"] for row in await conn.fetch("SELECT version FROM schema_migrations")
        }
        for migration_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            version = migration_file.name
            if version in already_applied:
                continue
            sql = migration_file.read_text(encoding="utf-8")
            async with conn.transaction():
                await conn.execute(sql)
                await conn.execute(
                    "INSERT INTO schema_migrations (version) VALUES ($1)", version
                )
            applied.append(version)
            logger.info("Applied migration %s", version)
    return applied


async def _main() -> None:
    logging.basicConfig(level=logging.INFO)
    from src.config import get_settings
    from src.infrastructure.postgres.pool import close_pool, create_pool

    settings = get_settings()
    pool = await create_pool(
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
        min_size=settings.postgres_pool_min_size,
        max_size=settings.postgres_pool_max_size,
    )
    try:
        applied = await run_migrations(pool)
    finally:
        await close_pool(pool)

    if applied:
        print(f"Applied {len(applied)} migration(s): {', '.join(applied)}")
    else:
        print("No new migrations to apply.")


if __name__ == "__main__":
    asyncio.run(_main())
