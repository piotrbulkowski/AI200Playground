"""Azure Blob Storage adapter. The only place azure-storage-blob / azure-identity are imported."""

from __future__ import annotations

from typing import IO

from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob import ContentSettings
from azure.storage.blob.aio import BlobServiceClient

from src.domain.document import BlobLocation


async def create_blob_service_client(
    account_url: str,
) -> tuple[BlobServiceClient, DefaultAzureCredential]:
    """DefaultAzureCredential only — az login locally, managed identity once Phase 8 wires it up.

    No connection strings or account keys: the storage account has shared_access_key_enabled=false.
    """
    credential = DefaultAzureCredential()
    client = BlobServiceClient(account_url=account_url, credential=credential)
    return client, credential


async def close_blob_service_client(
    client: BlobServiceClient, credential: DefaultAzureCredential
) -> None:
    await client.close()
    await credential.close()


class AzureBlobDocumentStore:
    def __init__(self, blob_service_client: BlobServiceClient, container: str) -> None:
        self._blob_service_client = blob_service_client
        self._container = container

    async def upload(
        self, *, blob_name: str, content: IO[bytes], content_type: str
    ) -> BlobLocation:
        container_client = self._blob_service_client.get_container_client(self._container)
        await container_client.upload_blob(
            name=blob_name,
            data=content,
            content_settings=ContentSettings(content_type=content_type),
            overwrite=True,
        )
        return BlobLocation(container=self._container, blob_name=blob_name)
