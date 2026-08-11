from __future__ import annotations

import io
from uuid import UUID

from src.application.commands import UploadDocumentCommand
from src.application.document_service import DocumentService
from src.domain.document import BlobLocation, Document, ProcessingStatus


class InMemoryDocumentRepository:
    """Fake of our own port — not a mock of the Azure/Postgres SDK."""

    def __init__(self) -> None:
        self.documents: dict[UUID, Document] = {}

    async def add(self, document: Document) -> None:
        self.documents[document.id] = document

    async def get(self, document_id: UUID) -> Document | None:
        return self.documents.get(document_id)

    async def list(self, *, limit: int, offset: int) -> list[Document]:
        ordered = sorted(self.documents.values(), key=lambda d: d.created_at, reverse=True)
        return ordered[offset : offset + limit]

    async def update(self, document: Document) -> None:
        self.documents[document.id] = document


class FakeBlobStore:
    def __init__(self) -> None:
        self.uploaded: list[tuple[str, str]] = []

    async def upload(self, *, blob_name: str, content, content_type: str) -> BlobLocation:
        self.uploaded.append((blob_name, content_type))
        return BlobLocation(container="documents", blob_name=blob_name)


def _command() -> UploadDocumentCommand:
    return UploadDocumentCommand(
        title="Networking fundamentals",
        category="networking",
        technology="azure-vnet",
        version="1.0",
        author="piotr",
        original_filename="networking.pdf",
        content_type="application/pdf",
        content=io.BytesIO(b"pdf bytes"),
    )


async def test_upload_document_writes_blob_then_persists_metadata():
    repository = InMemoryDocumentRepository()
    blob_store = FakeBlobStore()
    service = DocumentService(repository, blob_store)

    document = await service.upload_document(_command())

    assert document.processing_status == ProcessingStatus.UPLOADED
    assert document.blob_location is not None
    assert blob_store.uploaded == [(str(document.id), "application/pdf")]
    assert repository.documents[document.id] == document


async def test_get_document_returns_none_when_missing():
    service = DocumentService(InMemoryDocumentRepository(), FakeBlobStore())

    assert await service.get_document(UUID(int=0)) is None


async def test_list_documents_delegates_to_repository():
    repository = InMemoryDocumentRepository()
    blob_store = FakeBlobStore()
    service = DocumentService(repository, blob_store)
    await service.upload_document(_command())
    await service.upload_document(_command())

    documents = await service.list_documents(limit=1, offset=0)

    assert len(documents) == 1
