# AI-200 Playground — Azure AI Knowledge Hub

## 0. What this is

A from-scratch build of an **Azure AI Knowledge Hub** — a small system for managing technical documents and answering questions about them with RAG. The application itself is not the point. It exists to give you a reason to touch, configure, break, and fix every Azure service on the **AI-200: Developing AI Solutions on Azure** exam, in a realistic (if intentionally over-engineered) architecture.

**Do not optimize this for production quality.** Optimize it for exam-relevant hands-on reps. Where "simplest solution that works" and "solution that forces you to learn the AI-200-relevant concept" disagree, build the second one.

This spec was refined against ~60 real AI-200 exam questions (topic dumps + a Fabrikam Inc. case study) sampled from a question bank. Where the exam tests a specific, easy-to-miss detail — an ordering requirement, an RBAC role name, a Key Vault reference syntax, a Redis eviction policy — that detail is called out explicitly in the relevant phase file as **"What the exam actually asks."** Treat those callouts as the highest-priority parts of each phase: they are the gap between "I built a RAG app" and "I can pass AI-200."

## 1. How to use this spec

The project is split into phase files under `specs/`. Work through them roughly in order — each one builds on infrastructure/code from the previous ones. Don't implement everything in one pass; finish a phase, verify it, update docs, then move on (see the roadmap in [10-exercises-troubleshooting-roadmap.md](10-exercises-troubleshooting-roadmap.md)).

| File | Phase |
|---|---|
| [01-foundations-and-api.md](01-foundations-and-api.md) | Project skeleton, domain model, document API, Blob Storage upload |
| [02-cosmos-db.md](02-cosmos-db.md) | Cosmos DB for NoSQL: partitioning, indexing, vector search, change feed, Always Encrypted |
| [03-postgresql.md](03-postgresql.md) | PostgreSQL relational schema, pgvector, connection pooling, SQL injection |
| [04-eventing-pipeline.md](04-eventing-pipeline.md) | Blob → Event Grid → Function → Service Bus → worker |
| [05-search-and-rag.md](05-search-and-rag.md) | Unified retrieval interface, Cosmos vs. Postgres, RAG pipeline |
| [06-caching-redis.md](06-caching-redis.md) | Azure Managed Redis: cache-aside + Redis as a vector index |
| [07-containers-and-deployment.md](07-containers-and-deployment.md) | Docker, ACR, Container Apps, KEDA, AKS |
| [08-security-and-config.md](08-security-and-config.md) | Key Vault, Managed Identity, App Configuration |
| [09-observability.md](09-observability.md) | OpenTelemetry, Azure Monitor, KQL |
| [10-exercises-troubleshooting-roadmap.md](10-exercises-troubleshooting-roadmap.md) | Build order, exercises, troubleshooting playground, Definition of Done, AI-200 topic mapping |

## 2. AI-200 scope

Per the official study guide (https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-200):

* containerized solutions, Azure Container Registry, Azure Container Apps, KEDA, AKS
* Azure Cosmos DB for NoSQL, Azure Database for PostgreSQL, pgvector
* Azure Managed Redis, vector search, RAG
* Service Bus, Event Grid, Azure Functions
* Key Vault, App Configuration
* OpenTelemetry, KQL

Every phase file maps directly to one or more of these. If a piece of work doesn't map to this list or to infrastructure another phase needs, it's out of scope — don't build it just because it's interesting (see §7).

## 3. Domain: document Q&A

1. A user uploads a technical document.
2. The document is stored (Blob Storage) and its metadata is recorded.
3. The system detects the new document (event-driven, not synchronous).
4. The document is processed asynchronously: parsed, chunked, embedded.
5. Chunks + embeddings + metadata are written to **both** Cosmos DB and PostgreSQL.
6. Indexes needed for semantic/vector search are built.
7. A user asks a question.
8. The system performs semantic retrieval, filtered by metadata.
9. An LLM generates an answer via RAG, grounded in retrieved chunks, with cited sources.
10. Responses may be served from an Azure Managed Redis cache.

No real UI. A REST API with OpenAPI/Swagger is the whole "frontend" for the life of this project.

## 4. Technology

**Backend:** Python 3.x, FastAPI, Pydantic, official Azure SDKs, async-first wherever the SDK and framework allow it.

**Containers:** Docker, Azure Container Registry, Azure Container Apps (AKS as a later, optional variant).

**Azure services:** Blob Storage, Event Grid, Service Bus, Azure Functions, Cosmos DB for NoSQL, Azure Database for PostgreSQL + pgvector, Azure Managed Redis, Key Vault, App Configuration, Application Insights / Azure Monitor, OpenTelemetry.

**AI layer:** Azure OpenAI (or whichever embedding + generative model is currently available in Azure), behind a thin provider abstraction so no single vendor SDK leaks across the codebase.

## 5. Architectural principle

Don't build a monolith where every endpoint calls Azure SDKs directly. Separate the app into:

* API layer
* application/use-case layer
* domain layer
* infrastructure layer (Azure integrations)
* AI integrations

Don't over-abstract. Introduce an abstraction only where the app genuinely has to support more than one implementation of something:

* vector search provider (Cosmos / Postgres / Redis)
* embedding provider
* LLM provider
* document processor

Don't wrap every individual Azure SDK client in its own interface "for testability." That's busywork, not learning.

## 6. Repository structure

```
/src
  /api
  /application
  /domain
  /infrastructure
  /ai
  /workers
/functions
/tests
/infra
/docker
/docs
  /architecture
  /ai-200
  /kql
  /troubleshooting
  /experiments
/exercises
/specs
README.md
```

Treat this as a starting point, not dogma — if Python conventions suggest a better layout, use it, but keep the responsibility boundaries from §5 visible.

## 7. The golden rule

Don't build a "demo Azure AI app." Build an **educational lab** where you can:

* change configuration and observe the effect,
* deliberately break a component,
* observe the failure through logs/metrics/traces/portal/KQL,
* measure behavior (latency, RU cost, cache hit ratio),
* compare two approaches side by side,
* fix the problem,
* explain *why* the fix works.

If there's a choice between "simpler production-grade solution" and "solution that better exercises an AI-200 concept," take the second. Don't add functionality just because it's interesting — every non-trivial component must trace back to an AI-200 topic or support one that does.

## 8. Infrastructure as Code

Azure resources must be reproducible - IaC must be present. Use Terraform and/or Azure Developer CLI (`azd`); One `azd up` (or equivalent) should stand up everything a phase needs.

## 9. Local development & configuration profiles

Run locally with Docker Compose for API, worker, PostgreSQL, and Redis. For Cosmos DB, prefer the real Azure resource once you reach vector search / Change Feed.
Azure subscription with a monthly budget of 45 EUR is provided and can be used for learning.

Configuration profiles: `development`, `test`, `azure`. Externalize everything — no hardcoded endpoints, credentials, resource names, AI parameters, or vector-store selection.

## 10. Testing

* Unit tests for domain logic.
* Integration tests for PostgreSQL, Cosmos DB, Redis, retrieval, and the RAG pipeline, run against real (dev-tier) Azure resources rather than mocked SDKs — mocking the Azure SDK end-to-end teaches you the mock, not the service.

## 11. Documentation as the deliverable

The documentation matters as much as the code. Every major component gets a doc under `/docs/ai-200/<component>.md` answering:

1. What problem does this service solve?
2. Why is it used here?
3. How does the application use it?
4. What Azure concepts should I understand?
5. What can go wrong?
6. How do I troubleshoot it?
7. What should I know for AI-200? (include the exam-specific gotchas from the phase spec)

Finish each doc with an "AI-200 skills covered" checklist. The full topic-to-feature mapping lives in [10-exercises-troubleshooting-roadmap.md](10-exercises-troubleshooting-roadmap.md).
