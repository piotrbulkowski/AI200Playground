"""asyncpg-backed DocumentRepository. Raw parameterized SQL, no ORM."""

from __future__ import annotations

from uuid import UUID

import asyncpg

from src.domain.document import BlobLocation, Document, ProcessingStatus

_SELECT_COLUMNS = """
    id, title, original_filename, content_type, category, technology, version, author,
    processing_status, processing_error, blob_container, blob_name, created_at, updated_at
"""


class PostgresDocumentRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def add(self, document: Document) -> None:
        blob_location = _require_blob_location(document)
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO documents (
                    id, title, original_filename, content_type, category, technology, version,
                    author, processing_status, processing_error, blob_container, blob_name,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                """,
                document.id,
                document.title,
                document.original_filename,
                document.content_type,
                document.category,
                document.technology,
                document.version,
                document.author,
                document.processing_status.value,
                document.processing_error,
                blob_location.container,
                blob_location.blob_name,
                document.created_at,
                document.updated_at,
            )

    async def get(self, document_id: UUID) -> Document | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT {_SELECT_COLUMNS} FROM documents WHERE id = $1", document_id
            )
        return _row_to_document(row) if row is not None else None

    async def list(self, *, limit: int, offset: int) -> list[Document]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                f"SELECT {_SELECT_COLUMNS} FROM documents "
                "ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                limit,
                offset,
            )
        return [_row_to_document(row) for row in rows]

    async def update(self, document: Document) -> None:
        blob_location = _require_blob_location(document)
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE documents SET
                    title = $2, original_filename = $3, content_type = $4, category = $5,
                    technology = $6, version = $7, author = $8, processing_status = $9,
                    processing_error = $10, blob_container = $11, blob_name = $12, updated_at = $13
                WHERE id = $1
                """,
                document.id,
                document.title,
                document.original_filename,
                document.content_type,
                document.category,
                document.technology,
                document.version,
                document.author,
                document.processing_status.value,
                document.processing_error,
                blob_location.container,
                blob_location.blob_name,
                document.updated_at,
            )


def _require_blob_location(document: Document) -> BlobLocation:
    if document.blob_location is None:
        raise ValueError("Cannot persist a document without a blob_location")
    return document.blob_location


def _row_to_document(row: asyncpg.Record) -> Document:
    return Document(
        id=row["id"],
        title=row["title"],
        original_filename=row["original_filename"],
        content_type=row["content_type"],
        category=row["category"],
        technology=row["technology"],
        version=row["version"],
        author=row["author"],
        processing_status=ProcessingStatus(row["processing_status"]),
        processing_error=row["processing_error"],
        blob_location=BlobLocation(container=row["blob_container"], blob_name=row["blob_name"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
