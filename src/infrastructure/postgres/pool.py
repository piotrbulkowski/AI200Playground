from __future__ import annotations

import asyncpg


async def create_pool(
    *,
    host: str,
    port: int,
    database: str,
    user: str,
    password: str,
    min_size: int,
    max_size: int,
) -> asyncpg.Pool:
    return await asyncpg.create_pool(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        min_size=min_size,
        max_size=max_size,
    )


async def close_pool(pool: asyncpg.Pool) -> None:
    await pool.close()
