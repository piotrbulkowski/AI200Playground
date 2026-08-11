from __future__ import annotations

from fastapi import Request

from src.application.document_service import DocumentService
from src.config import Settings
from src.infrastructure.blob_storage import AzureBlobDocumentStore
from src.infrastructure.postgres.document_repository import PostgresDocumentRepository


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


def get_document_service(request: Request) -> DocumentService:
    state = request.app.state
    repository = PostgresDocumentRepository(state.pg_pool)
    blob_store = AzureBlobDocumentStore(
        state.blob_service_client, state.settings.azure_storage_container
    )
    return DocumentService(repository, blob_store)
