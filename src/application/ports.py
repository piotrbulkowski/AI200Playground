"""Ports the application layer depends on. Infrastructure provides the adapters.

Framework-free by design: no Azure SDK types and no web-framework types (e.g. FastAPI's
UploadFile) may appear in these signatures.
"""

from __future__ import annotations

from typing import IO, Protocol
from uuid import UUID

from src.domain.document import BlobLocation, Document


class DocumentRepository(Protocol):
    async def add(self, document: Document) -> None: ...

    async def get(self, document_id: UUID) -> Document | None: ...

    async def list(self, *, limit: int, offset: int) -> list[Document]: ...

    async def update(self, document: Document) -> None: ...


class BlobStoragePort(Protocol):
    async def upload(
        self, *, blob_name: str, content: IO[bytes], content_type: str
    ) -> BlobLocation: ...
