from __future__ import annotations

import io
from uuid import uuid4

import pytest

from src.infrastructure.blob_storage import (
    AzureBlobDocumentStore,
    close_blob_service_client,
    create_blob_service_client,
)

pytestmark = pytest.mark.integration


async def test_upload_writes_blob_to_the_real_storage_account(settings):
    client, credential = await create_blob_service_client(settings.azure_storage_account_url)
    store = AzureBlobDocumentStore(client, settings.azure_storage_container)
    blob_name = str(uuid4())

    try:
        location = await store.upload(
            blob_name=blob_name,
            content=io.BytesIO(b"hello from phase 1"),
            content_type="text/plain",
        )

        assert location.container == settings.azure_storage_container
        assert location.blob_name == blob_name

        container_client = client.get_container_client(settings.azure_storage_container)
        downloaded = await (await container_client.download_blob(blob_name)).readall()
        assert downloaded == b"hello from phase 1"
    finally:
        container_client = client.get_container_client(settings.azure_storage_container)
        await container_client.delete_blob(blob_name, delete_snapshots="include")
        await close_blob_service_client(client, credential)
