from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routers.documents import router as documents_router
from src.config import get_settings
from src.infrastructure.blob_storage import close_blob_service_client, create_blob_service_client
from src.infrastructure.postgres.migrations import run_migrations
from src.infrastructure.postgres.pool import close_pool, create_pool


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.settings = settings

    pg_pool = await create_pool(
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
        min_size=settings.postgres_pool_min_size,
        max_size=settings.postgres_pool_max_size,
    )
    await run_migrations(pg_pool)
    app.state.pg_pool = pg_pool

    blob_service_client, blob_credential = await create_blob_service_client(
        settings.azure_storage_account_url
    )
    app.state.blob_service_client = blob_service_client
    app.state.blob_credential = blob_credential

    try:
        yield
    finally:
        await close_pool(pg_pool)
        await close_blob_service_client(blob_service_client, blob_credential)


def create_app() -> FastAPI:
    app = FastAPI(title="AI-200 Playground — Document API", lifespan=lifespan)
    app.include_router(documents_router)
    return app


app = create_app()
