# AI-200 Playground — Azure AI Knowledge Hub

A hands-on lab for the **AI-200: Developing AI Solutions on Azure** exam, built as a document Q&A / RAG system. See [`specs/00-overview.md`](specs/00-overview.md) for the full design and [`specs/10-exercises-troubleshooting-roadmap.md`](specs/10-exercises-troubleshooting-roadmap.md) for build order. This README covers what's built so far (Phase 1).

## Prerequisites

* [uv](https://docs.astral.sh/uv/)
* Docker (for local Postgres)
* Terraform + an Azure subscription, logged in via `az login`

## Setup

```bash
uv sync
cp .env.example .env   # adjust as needed
```

### Provision Azure Storage

```bash
cd infra
terraform init
terraform apply
```

Copy the `storage_account_blob_endpoint` output into `.env` as `AZURE_STORAGE_ACCOUNT_URL` if it differs from the default. Auth is `DefaultAzureCredential` — make sure you're logged in with `az login` and have been granted **Storage Blob Data Contributor** (the Terraform config grants this to whoever runs `apply`, or to `developer_object_id` if set).

The storage account is created with `shared_access_key_enabled = false` (no account keys — AAD auth only). This means `provider "azurerm"` must set `storage_use_azuread = true` (see `infra/providers.tf`); without it, `terraform apply` creates the storage account successfully but then fails with `403 KeyBasedAuthenticationNotPermitted` while polling for the blob service to become available, because the provider's own readiness check tries key-based auth by default.

### Start Postgres and run migrations

```bash
docker compose up -d postgres
uv run python -m src.infrastructure.postgres.migrations
```

`docker/postgres-init/001-create-test-db.sql` creates the `ai200_test` database (used by the
`test` config profile) automatically, but only on a fresh `postgres-data` volume. If you already
had the volume from before this existed, create it once by hand:
`docker exec <postgres-container> psql -U ai200 -d ai200_dev -c "CREATE DATABASE ai200_test"`.

### Run the API

```bash
uv run fastapi dev src/api/main.py
```

Swagger UI: http://127.0.0.1:8000/docs

## Tests

```bash
uv run pytest                # unit + guardrail tests only
uv run pytest -m integration # hits the real Storage account + Postgres
```

## Layering

```
src/api             FastAPI routes/schemas — thin, delegates to application
src/application     use-cases, ports (DocumentRepository, BlobStoragePort)
src/domain          pure entities/logic — no Azure SDK, no asyncpg, no FastAPI
src/infrastructure  Azure Blob Storage, Postgres — the only place SDK imports live
src/ai              embedding/LLM provider abstractions (Phase 5+)
src/workers         async document processing (Phase 4+)
```

`tests/guardrails/` enforces this: `test_layering.py` fails the build if `src/domain` imports anything it shouldn't; `test_async_boundary.py` fails if the upload endpoint's code path starts doing inline processing (parsing/chunking/embedding) instead of handing off to the future event-driven pipeline.
