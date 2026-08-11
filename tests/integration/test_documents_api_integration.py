from __future__ import annotations

import io

import httpx
import pytest

from src.api.main import create_app

pytestmark = pytest.mark.integration


async def test_upload_then_fetch_document_and_status():
    app = create_app()
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/documents",
                data={
                    "title": "Networking fundamentals",
                    "category": "networking",
                    "technology": "azure-vnet",
                    "version": "1.0",
                    "author": "piotr",
                },
                files={"file": ("networking.pdf", io.BytesIO(b"pdf bytes"), "application/pdf")},
            )
            assert response.status_code == 201
            document_id = response.json()["id"]

            status_response = await client.get(f"/documents/{document_id}/status")
            assert status_response.status_code == 200
            assert status_response.json()["processing_status"] == "uploaded"

            get_response = await client.get(f"/documents/{document_id}")
            assert get_response.status_code == 200
            assert get_response.json()["title"] == "Networking fundamentals"

            list_response = await client.get("/documents")
            assert list_response.status_code == 200
            assert any(item["id"] == document_id for item in list_response.json()["items"])


async def test_get_document_returns_404_when_missing():
    app = create_app()
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/documents/00000000-0000-0000-0000-000000000000")
            assert response.status_code == 404


async def test_upload_rejects_unsupported_content_type():
    app = create_app()
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/documents",
                data={
                    "title": "Suspicious",
                    "category": "networking",
                    "technology": "azure-vnet",
                    "version": "1.0",
                    "author": "piotr",
                },
                files={"file": ("payload.exe", io.BytesIO(b"MZ"), "application/x-msdownload")},
            )
            assert response.status_code == 422
