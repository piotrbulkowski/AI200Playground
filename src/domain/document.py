"""Pure domain model for documents. No Azure SDK, asyncpg, or web-framework imports here."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel


class ProcessingStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


_ALLOWED_TRANSITIONS: dict[ProcessingStatus, set[ProcessingStatus]] = {
    ProcessingStatus.UPLOADED: {ProcessingStatus.PROCESSING},
    ProcessingStatus.PROCESSING: {ProcessingStatus.INDEXED, ProcessingStatus.FAILED},
    ProcessingStatus.INDEXED: set(),
    ProcessingStatus.FAILED: set(),
}


class InvalidStatusTransition(Exception):
    def __init__(self, current: ProcessingStatus, target: ProcessingStatus) -> None:
        super().__init__(f"Cannot transition document from {current.value!r} to {target.value!r}")
        self.current = current
        self.target = target


class BlobLocation(BaseModel):
    container: str
    blob_name: str


class Document(BaseModel):
    id: UUID
    title: str
    original_filename: str
    content_type: str
    category: str
    technology: str
    version: str
    author: str
    created_at: datetime
    updated_at: datetime
    processing_status: ProcessingStatus
    processing_error: str | None = None
    blob_location: BlobLocation | None = None

    @classmethod
    def new(
        cls,
        *,
        title: str,
        original_filename: str,
        content_type: str,
        category: str,
        technology: str,
        version: str,
        author: str,
    ) -> Document:
        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            title=title,
            original_filename=original_filename,
            content_type=content_type,
            category=category,
            technology=technology,
            version=version,
            author=author,
            created_at=now,
            updated_at=now,
            processing_status=ProcessingStatus.UPLOADED,
        )

    def with_blob_location(self, blob_location: BlobLocation) -> Document:
        return self.model_copy(
            update={"blob_location": blob_location, "updated_at": datetime.now(UTC)}
        )

    def mark_processing(self) -> Document:
        return self._transition_to(ProcessingStatus.PROCESSING)

    def mark_indexed(self) -> Document:
        return self._transition_to(ProcessingStatus.INDEXED)

    def mark_failed(self, error: str) -> Document:
        document = self._transition_to(ProcessingStatus.FAILED)
        return document.model_copy(update={"processing_error": error})

    def _transition_to(self, target: ProcessingStatus) -> Document:
        if target not in _ALLOWED_TRANSITIONS[self.processing_status]:
            raise InvalidStatusTransition(self.processing_status, target)
        return self.model_copy(
            update={"processing_status": target, "updated_at": datetime.now(UTC)}
        )
