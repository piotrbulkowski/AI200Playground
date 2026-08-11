from __future__ import annotations

from datetime import timedelta

import pytest

from src.domain.document import BlobLocation, Document, ProcessingStatus
from src.infrastructure.postgres.document_repository import PostgresDocumentRepository

pytestmark = pytest.mark.integration


def _document() -> Document:
    document = Document.new(
        title="Networking fundamentals",
        original_filename="networking.pdf",
        content_type="application/pdf",
        category="networking",
        technology="azure-vnet",
        version="1.0",
        author="piotr",
    )
    location = BlobLocation(container="documents-test", blob_name=str(document.id))
    return document.with_blob_location(location)


async def test_add_and_get_round_trip(pg_pool):
    repository = PostgresDocumentRepository(pg_pool)
    document = _document()

    await repository.add(document)
    fetched = await repository.get(document.id)

    assert fetched == document


async def test_get_returns_none_when_missing(pg_pool):
    repository = PostgresDocumentRepository(pg_pool)

    assert await repository.get(_document().id) is None


async def test_list_orders_by_created_at_desc(pg_pool):
    # Explicit, distinct timestamps — real-clock resolution can tie two back-to-back inserts.
    repository = PostgresDocumentRepository(pg_pool)
    first = _document()
    second = _document().model_copy(
        update={"created_at": first.created_at + timedelta(seconds=1)}
    )
    await repository.add(first)
    await repository.add(second)

    documents = await repository.list(limit=10, offset=0)

    assert [document.id for document in documents] == [second.id, first.id]


async def test_update_persists_status_transition(pg_pool):
    repository = PostgresDocumentRepository(pg_pool)
    document = _document()
    await repository.add(document)

    updated = document.mark_processing()
    await repository.update(updated)

    fetched = await repository.get(document.id)
    assert fetched.processing_status == ProcessingStatus.PROCESSING
