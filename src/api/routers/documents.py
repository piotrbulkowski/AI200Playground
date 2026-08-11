"""Document endpoints. Upload validates + hands off to Blob Storage + Postgres and returns —
no parsing/chunking/embedding happens on this path. See tests/guardrails/test_async_boundary.py."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Response, UploadFile, status

from src.api.deps import get_document_service, get_settings_dep
from src.api.schemas.documents import (
    DocumentListResponse,
    DocumentResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
)
from src.application.commands import UploadDocumentCommand
from src.application.document_service import DocumentService
from src.config import Settings

router = APIRouter(prefix="/documents", tags=["documents"])


def _validate_upload(file: UploadFile, settings: Settings) -> None:
    if file.content_type not in settings.allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Unsupported content type: {file.content_type}",
        )
    max_bytes = settings.upload_max_size_mb * 1024 * 1024
    if file.size is not None and file.size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"File exceeds the {settings.upload_max_size_mb}MB limit",
        )


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    response: Response,
    file: UploadFile,
    title: str = Form(...),
    category: str = Form(...),
    technology: str = Form(...),
    version: str = Form(...),
    author: str = Form(...),
    document_service: DocumentService = Depends(get_document_service),
    settings: Settings = Depends(get_settings_dep),
) -> DocumentUploadResponse:
    _validate_upload(file, settings)
    command = UploadDocumentCommand(
        title=title,
        category=category,
        technology=technology,
        version=version,
        author=author,
        original_filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
        content=file.file,
    )
    document = await document_service.upload_document(command)
    response.headers["Location"] = f"/documents/{document.id}"
    return DocumentUploadResponse.from_domain(document)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    document = await document_service.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentResponse.from_domain(document)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    limit: int = 50,
    offset: int = 0,
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse:
    documents = await document_service.list_documents(limit=limit, offset=offset)
    return DocumentListResponse.from_domain(documents, limit=limit, offset=offset)


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: UUID,
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentStatusResponse:
    document = await document_service.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentStatusResponse.from_domain(document)
