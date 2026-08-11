"""API request/response contracts. Deliberately distinct from src.domain.document.Document so
the two can diverge independently as later phases add fields the API doesn't need to expose."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.domain.document import Document, ProcessingStatus


class DocumentResponse(BaseModel):
    id: UUID
    title: str
    original_filename: str
    content_type: str
    category: str
    technology: str
    version: str
    author: str
    processing_status: ProcessingStatus
    processing_error: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, document: Document) -> DocumentResponse:
        return cls(
            id=document.id,
            title=document.title,
            original_filename=document.original_filename,
            content_type=document.content_type,
            category=document.category,
            technology=document.technology,
            version=document.version,
            author=document.author,
            processing_status=document.processing_status,
            processing_error=document.processing_error,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )


class DocumentUploadResponse(DocumentResponse):
    pass


class DocumentStatusResponse(BaseModel):
    id: UUID
    processing_status: ProcessingStatus
    processing_error: str | None
    updated_at: datetime

    @classmethod
    def from_domain(cls, document: Document) -> DocumentStatusResponse:
        return cls(
            id=document.id,
            processing_status=document.processing_status,
            processing_error=document.processing_error,
            updated_at=document.updated_at,
        )


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    limit: int
    offset: int

    @classmethod
    def from_domain(
        cls, documents: list[Document], *, limit: int, offset: int
    ) -> DocumentListResponse:
        return cls(
            items=[DocumentResponse.from_domain(document) for document in documents],
            limit=limit,
            offset=offset,
        )
