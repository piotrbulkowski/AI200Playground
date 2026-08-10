# Phase 1 — Foundations, Domain Model, API, Blob Storage

## Goal

Stand up the project skeleton, the `Document` domain concept, and the upload path down to Blob Storage — nothing async yet. This phase exists to get the layering right (§5 of the overview) before there's event-driven complexity layered on top of it.

## AI-200 topics covered

Azure Blob Storage fundamentals; the "don't do heavy work in the request thread" pattern that every later async-processing question assumes you already understand.

## What you'll build

* Project skeleton: `src/api`, `src/application`, `src/domain`, `src/infrastructure`, `src/ai`, `src/workers`, `tests`, Python tooling (uv/poetry, ruff, pytest, pydantic-settings).
* `Document` domain entity with at least: `id`, `title`, `original_filename`, `content_type`, `category`, `technology`, `version`, `author`, `created_at`, `updated_at`, `processing_status`, `processing_error`, `blob_location`.
* `processing_status`: `uploaded → processing → indexed | failed`.
* Endpoints: `POST /documents` (upload), `GET /documents/{id}`, `GET /documents`, `GET /documents/{id}/status`.
* Blob Storage integration: on upload, the API (1) validates metadata, (2) writes the file to Blob Storage, (3) persists document metadata, (4) returns — and stops. No parsing, chunking, or embedding happens inline.

## Requirements

* The upload endpoint must return as soon as the blob and metadata record exist. It hands off to the event-driven pipeline built in Phase 4 — for now it's fine for the document to just sit in `uploaded` status with nothing consuming it yet; that's the seam Phase 4 plugs into.
* Keep the domain layer free of Azure SDK imports. The API layer and infrastructure layer are the only places `azure-storage-blob` etc. should appear.
* Use a proper Pydantic settings model for configuration from day one (env vars now, App Configuration/Key Vault plug in during Phase 8) — retrofitting this later is exactly the kind of busywork this project isn't about.

## Exercises

* **Enforce the async boundary.** Add a test that fails the build if the upload endpoint's handler function makes any call that isn't storage/metadata (e.g., grep-based or import-boundary test). This is the guardrail that keeps Phase 4 honest later.

## Definition of done

* `POST /documents` accepts a file + metadata, stores the blob, persists a document record, and returns quickly regardless of file size.
* `GET /documents/{id}/status` reflects `uploaded`.
* OpenAPI/Swagger UI is up and documents all four endpoints.
* `/docs/ai-200/blob-storage.md` written per the template in the overview.

Next: [02-cosmos-db.md](02-cosmos-db.md).
