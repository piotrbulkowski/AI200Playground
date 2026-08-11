"""Use-case orchestration for documents.

Upload path is deliberately shallow: validate metadata, write the blob, persist the
record, return. No parsing/chunking/embedding happens here — that's Phase 4's
event-driven pipeline. `tests/guardrails/test_async_boundary.py` enforces this.
"""

from __future__ import annotations

from uuid import UUID

from src.application.commands import UploadDocumentCommand
from src.application.ports import BlobStoragePort, DocumentRepository
from src.domain.document import Document


class DocumentService:
    def __init__(self, repository: DocumentRepository, blob_store: BlobStoragePort) -> None:
        self._repository = repository
        self._blob_store = blob_store

    async def upload_document(self, command: UploadDocumentCommand) -> Document:
        document = Document.new(
            title=command.title,
            original_filename=command.original_filename,
            content_type=command.content_type,
            category=command.category,
            technology=command.technology,
            version=command.version,
            author=command.author,
        )
        blob_location = await self._blob_store.upload(
            blob_name=str(document.id),
            content=command.content,
            content_type=command.content_type,
        )
        document = document.with_blob_location(blob_location)
        await self._repository.add(document)
        return document

    async def get_document(self, document_id: UUID) -> Document | None:
        return await self._repository.get(document_id)

    async def list_documents(self, *, limit: int, offset: int) -> list[Document]:
        return await self._repository.list(limit=limit, offset=offset)
