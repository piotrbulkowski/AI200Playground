from __future__ import annotations

import pytest

from src.domain.document import BlobLocation, Document, InvalidStatusTransition, ProcessingStatus


def _new_document() -> Document:
    return Document.new(
        title="Networking fundamentals",
        original_filename="networking.pdf",
        content_type="application/pdf",
        category="networking",
        technology="azure-vnet",
        version="1.0",
        author="piotr",
    )


def test_new_document_starts_uploaded_with_no_blob_location():
    document = _new_document()

    assert document.processing_status == ProcessingStatus.UPLOADED
    assert document.blob_location is None
    assert document.processing_error is None


def test_with_blob_location_attaches_location_without_changing_status():
    document = _new_document()
    location = BlobLocation(container="documents", blob_name=str(document.id))

    updated = document.with_blob_location(location)

    assert updated.blob_location == location
    assert updated.processing_status == ProcessingStatus.UPLOADED


def test_legal_transition_uploaded_to_processing_to_indexed():
    document = _new_document().mark_processing()
    assert document.processing_status == ProcessingStatus.PROCESSING

    document = document.mark_indexed()
    assert document.processing_status == ProcessingStatus.INDEXED


def test_legal_transition_processing_to_failed_records_error():
    document = _new_document().mark_processing().mark_failed("parser blew up")

    assert document.processing_status == ProcessingStatus.FAILED
    assert document.processing_error == "parser blew up"


def test_illegal_transition_uploaded_to_indexed_raises():
    document = _new_document()

    with pytest.raises(InvalidStatusTransition):
        document.mark_indexed()


def test_illegal_transition_from_terminal_state_raises():
    document = _new_document().mark_processing().mark_indexed()

    with pytest.raises(InvalidStatusTransition):
        document.mark_processing()
