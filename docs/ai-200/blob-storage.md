# Azure Blob Storage

## 1. What problem does this service solve?

Documents uploaded through `POST /documents` can be arbitrarily large and arrive in binary
formats (PDF, plain text, Markdown, JSON in this project). Storing that content in a relational
or document database is the wrong tool — Blob Storage is Azure's object store, built for large,
unstructured binary payloads with cheap capacity and durable, tiered storage. Everything else
in the pipeline (metadata records, chunks, embeddings, indexes) references a document by
pointing at its blob, not by embedding the file bytes.

## 2. Why is it used here?

This project's domain (§3 of `specs/00-overview.md`) needs a durable place to land the raw
uploaded file the moment it arrives, decoupled from the metadata store (PostgreSQL, later also
Cosmos DB) and from the eventual event-driven processing pipeline (Phase 4). Blob Storage plays
that role: it's the one thing everything else in the pipeline eventually points back to.

## 3. How does the application use it?

* `src/infrastructure/blob_storage.py::AzureBlobDocumentStore` wraps the async
  `azure-storage-blob` `BlobServiceClient` and implements the `BlobStoragePort` protocol
  (`src/application/ports.py`) — the only method needed for Phase 1 is `upload`.
* `create_blob_service_client()` builds the client with `azure.identity.aio.DefaultAzureCredential`
  — no connection string or account key exists anywhere in this project (the storage account is
  provisioned with `shared_access_key_enabled = false` in `infra/storage.tf`, so account keys
  can't even be issued).
* The client and its credential are created once in `src/api/main.py`'s FastAPI `lifespan`,
  stored on `app.state`, and closed on shutdown — not created per-request.
* `DocumentService.upload_document` (`src/application/document_service.py`) calls
  `blob_store.upload(...)` with the raw file-like object from the multipart upload, gets back a
  `BlobLocation` (container + blob name), attaches it to the `Document`, and persists the
  metadata record. Nothing else happens on this path — no parsing, chunking, or embedding. That
  boundary is enforced by `tests/guardrails/test_async_boundary.py`, not just convention.
* Two containers exist: `documents` (real data) and `documents-test` (integration tests), so
  tests never touch dev blobs.

## 4. What Azure concepts should I understand?

* **Containers** — the blob namespace unit; access is scoped per-container
  (`container_access_type = "private"` here — no anonymous read).
* **Data-plane vs. management-plane RBAC** — being an Owner/Contributor on the storage account
  (management plane, can reconfigure the account) is different from being able to read/write
  blobs (data plane). This project grants only the data-plane role: **Storage Blob Data
  Contributor**, scoped to the storage account, via `infra/rbac.tf`.
* **Auth options** — account keys (shared secret, full access, hard to scope/rotate),
  connection strings (embed the key), SAS tokens (time-boxed, scopable), and Azure AD /
  `DefaultAzureCredential` (identity-based, revocable via RBAC, no secret to leak). This project
  uses the last one exclusively — see §6 below for why.
* **`DefaultAzureCredential`** — tries a chain of credential sources in order (environment vars,
  workload identity, managed identity, Azure CLI login, etc.) and uses the first that works.
  Locally that's your `az login` session; once Phase 8 adds Managed Identity for the deployed
  app, no code changes — the same `DefaultAzureCredential` call picks it up automatically.
* **Async SDK client lifecycle** — the async `azure-storage-blob`/`azure-identity` clients hold
  open HTTP connections (via `aiohttp`) and must be explicitly closed (`await client.close()`),
  which is why they're created once at startup and closed in the `lifespan` shutdown path rather
  than per-request.
* **The "don't do heavy work in the request thread" pattern** — the upload endpoint validates,
  writes the blob, writes the metadata row, and returns, regardless of file size. Parsing/
  chunking/embedding is Phase 4's job, triggered by Blob Storage's own eventing (Event Grid),
  not by this request.

## 5. What can go wrong?

* **403 Forbidden on upload/read** — almost always a missing or wrong RBAC role assignment
  (see troubleshooting below), not a code bug.
* **Auth works locally, fails when deployed** — `DefaultAzureCredential`'s credential chain
  found a *different* identity locally (your `az login`) than it will in a deployed environment
  (a managed identity, added in Phase 8). Each identity needs its own role assignment.
  Storage account access at all — a missing/incomplete RBAC role propagation delay (assignments
  can take a couple of minutes to take effect) looks identical to a missing role at first glance.
* **Slow uploads block the whole request** — if validation logic starts reading/buffering the
  entire file before the blob write begins, large files will make `POST /documents` slow
  regardless of async I/O; validation here is limited to O(1) checks (content-type, `Content-Length`).
* **Uploading to the wrong container** — `test` config profile targets `documents-test`; if a
  test ever runs against `development`'s settings by mistake, it pollutes real dev data.
* **`terraform apply` fails right after creating the storage account** — with
  `shared_access_key_enabled = false`, the azurerm provider's own post-create "wait for the blob
  service to become available" check polls using key-based auth by default and fails with `403
  KeyBasedAuthenticationNotPermitted`, even though the storage account itself was created
  successfully. Fix: `provider "azurerm" { storage_use_azuread = true }` (see
  `infra/providers.tf`) so that check uses Azure AD instead. Don't assume the resource failed to
  create — verify with `az storage account show` before troubleshooting further.

## 6. How do I troubleshoot it?

1. **Confirm identity**: `az account show` — which identity will `DefaultAzureCredential` pick
   up locally?
2. **Confirm role assignment**: `az role assignment list --scope <storage-account-resource-id>
   --query "[].{principal:principalId, role:roleDefinitionName}"` — is your object ID listed
   against `Storage Blob Data Contributor`?
3. **Confirm the account itself**: `shared_access_key_enabled` should be `false` (Portal →
   Storage account → Configuration, or `az storage account show --query
   allowSharedKeyAccess`) — if `true`, someone bypassed Terraform and the account drifted from
   the IaC definition.
4. **Reproduce outside the app**: `az storage blob list --account-name <name> --container-name
   documents --auth-mode login` — isolates "is this an Azure/RBAC problem" from "is this an
   application bug."
5. **Application Insights / logs** (once Phase 9 wires up observability): the Azure SDK raises a
   typed `azure.core.exceptions.ClientAuthenticationError` / `HttpResponseError` with a status
   code and `x-ms-request-id` — always check the status code first (401 vs. 403 vs. 404 mean
   different things: no credential found, credential found but unauthorized, container/blob
   doesn't exist).

## 7. What should I know for AI-200?

* Blob Storage access tiers (Hot/Cool/Cold/Archive) and when each applies — not exercised by
  Phase 1's code, but a direct exam topic: know the retrieval-latency/cost tradeoff.
* The difference between an **account key**, a **SAS token**, and **Azure AD (RBAC) auth** for
  data-plane access — and specifically that `shared_access_key_enabled = false` is how you
  *prevent* account-key auth from being possible at all, not just discourage it.
* Data-plane built-in roles: **Storage Blob Data Owner** / **Contributor** / **Reader** — know
  which operations each permits, and that they're distinct from the control-plane
  Owner/Contributor/Reader roles on the resource itself.
* `DefaultAzureCredential`'s credential chain order, and that it's the same call site whether
  you're running locally (`az login`) or deployed (Managed Identity) — this is precisely the
  credential-free-everywhere pattern Phase 8 formalizes.
* Container access levels (private / blob / container) and why "private" is the default you
  want for anything that isn't meant to be publicly browsable.
* The general pattern this phase exists to teach: **accept work fast, do the actual work
  asynchronously** — the same shape reappears with Event Grid + Functions (Phase 4), Service Bus
  (Phase 4), and KEDA-driven autoscaling (Phase 7).

## AI-200 skills covered

- [x] Blob Storage containers and access levels
- [x] Data-plane RBAC roles vs. management-plane roles
- [x] Account keys / SAS / Azure AD auth tradeoffs, and disabling shared-key auth
- [x] `DefaultAzureCredential` and the local-dev-to-managed-identity migration path
- [x] Async Azure SDK client lifecycle management
- [x] The "return fast, process asynchronously" architectural pattern
- [ ] Access tiers (Hot/Cool/Cold/Archive) and lifecycle management — not exercised by code yet;
      concept only
