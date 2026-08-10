# Phase 10 — Exercises, Troubleshooting, Roadmap, AI-200 Mapping

This file ties the previous nine together: the order to build them in, a bank of self-contained exercises, a troubleshooting playground, and the full AI-200 topic mapping. Treat it as the thing you come back to after each phase, not something to build once at the end.

## Build order

Work in this order; each step assumes the previous ones are done and working. After each step: run the tests, verify the config, update the README, update the relevant `/docs/ai-200/*.md`, and don't move on until the current step actually works.

1. Project skeleton + Python tooling.
2. Domain model + API ([01](01-foundations-and-api.md)).
3. Blob Storage upload path ([01](01-foundations-and-api.md)).
4. Cosmos DB integration: partitioning, indexing, consistency, Always Encrypted stretch ([02](02-cosmos-db.md)).
5. PostgreSQL relational schema ([03](03-postgresql.md)).
6. Event Grid + Azure Function ([04](04-eventing-pipeline.md)).
7. Service Bus + document processing worker ([04](04-eventing-pipeline.md)).
8. Embeddings + pgvector ([03](03-postgresql.md)).
9. Cosmos DB vector search + Change Feed ([02](02-cosmos-db.md)).
10. Unified retrieval interface across Cosmos/Postgres ([05](05-search-and-rag.md)).
11. RAG pipeline ([05](05-search-and-rag.md)).
12. Redis cache-aside ([06](06-caching-redis.md)).
13. Redis vector index ([06](06-caching-redis.md)).
14. Docker images + Azure Container Registry + ACR Tasks ([07](07-containers-and-deployment.md)).
15. Azure Container Apps deployment ([07](07-containers-and-deployment.md)).
16. KEDA autoscaling ([07](07-containers-and-deployment.md)).
17. Key Vault + Managed Identity ([08](08-security-and-config.md)).
18. App Configuration ([08](08-security-and-config.md)).
19. OpenTelemetry + Azure Monitor ([09](09-observability.md)).
20. KQL playground ([09](09-observability.md)).
21. AKS deployment of the worker ([07](07-containers-and-deployment.md)).
22. Exercises + troubleshooting scenarios (this file).
23. Final AI-200 mapping/documentation pass (this file).

## Exercises

Each exercise should force you to actually diagnose something, not follow a recipe. Where possible, plant the bug yourself (a script, a feature flag, a deliberately wrong config value) so you can reset and redo it later.

* **Cosmos RU optimization** — a document query burns too much RU. Find the missing composite index (or the badly-chosen partition key) and fix it. ([02](02-cosmos-db.md))
* **Cosmos consistency tradeoff** — given a scenario requirement (e.g. "reads must reflect the writer's own prior writes, but don't need global strong ordering"), pick and justify the cheapest sufficient consistency level from the five. ([02](02-cosmos-db.md))
* **PostgreSQL vector performance** — semantic search is too slow. Diagnose the pgvector indexing problem (wrong/missing index type, missing metadata index, index built before bulk load) and fix it. ([03](03-postgresql.md))
* **SQL injection** — exploit a raw-SQL endpoint, then patch it with parameterized queries. ([03](03-postgresql.md))
* **Service Bus DLQ** — the worker silently stops processing some documents. Find them in the DLQ, determine the root cause, and reprocess. ([04](04-eventing-pipeline.md))
* **Event Grid non-retriable failure** — configure an endpoint that returns 400 for a specific payload and confirm events land in the dead-letter destination instead of being silently dropped. ([04](04-eventing-pipeline.md))
* **KEDA scale mismatch** — the queue grows faster than the worker drains it. Diagnose and fix the `ScaledObject` (threshold, max replicas, polling interval). ([07](07-containers-and-deployment.md))
* **AKS connectivity** — break a service selector, a container startup command, and a readiness probe, one at a time; diagnose each using the matrix in [07](07-containers-and-deployment.md).
* **Key Vault / Managed Identity** — after a deployment, the app can't fetch a secret. Determine whether it's a missing identity, wrong role, or wrong scope. ([08](08-security-and-config.md))
* **App Configuration environment drift** — a setting has the wrong value in one environment because the label wasn't set correctly. Find and fix it. ([08](08-security-and-config.md))
* **OpenTelemetry blind spot** — an outbound HTTP call isn't showing up connected to its parent trace. Find the missing instrumentation. ([09](09-observability.md))
* **RAG latency** — a `/ask` request is slow. Use a trace to find the actual bottleneck component. ([09](09-observability.md))

## Troubleshooting playground

Beyond the scoped exercises above, keep a running set of injectable failures you can toggle for practice sessions:

* Wrong Service Bus connection info.
* PostgreSQL unreachable (wrong host/port/credentials, or connection pool exhausted).
* Malformed Cosmos DB query (missing index dependency, bad partition key filter).
* Cache failure (Redis unreachable, wrong eviction policy for the scenario).
* Misconfigured Managed Identity (missing role assignment, wrong scope).
* A poisoned message that always fails processing.
* A wrong/missing environment variable.
* A bad Container Apps revision (broken image, missing secret).
* An AKS connectivity break (see exercise above).

For each: observe the failure through logs, metrics, traces, the Azure portal, and a KQL query — that's the point of Phase 9's investment.

## Definition of Done

The project is complete when:

* The app runs locally; API and worker each run as separate containers.
* A document can be uploaded, lands in Blob Storage, and Event Grid detects it.
* The Azure Function publishes a processing message to Service Bus; the worker processes it.
* The document is stored in both Cosmos DB and PostgreSQL, with embeddings generated.
* PostgreSQL + pgvector and Cosmos DB can both perform semantic search; Redis can too, as a third backend behind the same interface.
* RAG produces answers with cited sources, and an explicit "insufficient context" response when nothing relevant is found.
* Service Bus retry/DLQ and Cosmos DB Change Feed both work and have been demonstrated, not just configured.
* Container Apps hosts API and worker; KEDA scales the worker off queue depth, including scale-to-zero.
* Key Vault, Managed Identity, and App Configuration are all in real use — no secrets in the repo.
* OpenTelemetry produces connected cross-service traces in Azure Monitor; the KQL playground works against real telemetry.
* An AKS deployment variant of the worker exists, with a diagnostic runbook.
* The troubleshooting exercises and playground scenarios are all reproducible.
* Every topic in the mapping table below has a corresponding, working piece of this project behind it.

## AI-200 topic mapping

| AI-200 topic | Playground feature | Phase |
|---|---|---|
| Cosmos DB SDK | Document/chunk repository | [02](02-cosmos-db.md) |
| Cosmos indexing (incl. composite indexes) | RU optimization experiment | [02](02-cosmos-db.md) |
| Cosmos consistency levels | Consistency-level experiment | [02](02-cosmos-db.md) |
| Cosmos vector search | Cosmos retrieval provider | [02](02-cosmos-db.md) |
| Cosmos Change Feed | Multi-instance lease-container processor | [02](02-cosmos-db.md) |
| Cosmos client-side encryption (Always Encrypted) | Encrypted field stretch exercise | [02](02-cosmos-db.md) |
| PostgreSQL schema design | Relational model | [03](03-postgresql.md) |
| pgvector (IVFFlat & HNSW) | PostgreSQL retrieval provider | [03](03-postgresql.md) |
| Metadata filtering + vector search | RAG retrieval (all backends) | [05](05-search-and-rag.md) |
| Connection pooling | PostgreSQL pool experiment | [03](03-postgresql.md) |
| SQL injection prevention | Parameterized-query exercise | [03](03-postgresql.md) |
| Event Grid subscriptions/filters/retry/DLQ | Document-event pipeline | [04](04-eventing-pipeline.md) |
| Azure Functions triggers/bindings/hosting plans | Event handler Function | [04](04-eventing-pipeline.md), [07](07-containers-and-deployment.md) |
| Service Bus queues/DLQ/duplicate detection/sessions | Document processing queue | [04](04-eventing-pipeline.md) |
| Redis caching (cache-aside, eviction policy) | RAG cache | [06](06-caching-redis.md) |
| Redis vector index | Redis retrieval provider | [06](06-caching-redis.md) |
| Container Registry + ACR Tasks | Image lifecycle | [07](07-containers-and-deployment.md) |
| Container Apps (revisions, ingress, custom domain, image pull auth) | API/worker deployment | [07](07-containers-and-deployment.md) |
| KEDA | Worker + API autoscaling | [07](07-containers-and-deployment.md) |
| AKS | Alternative worker deployment | [07](07-containers-and-deployment.md) |
| App Service container hosting (concept parity) | App Service concept note | [07](07-containers-and-deployment.md) |
| Key Vault + RBAC | Secret management | [08](08-security-and-config.md) |
| Managed Identity | Credential-free auth everywhere | [08](08-security-and-config.md) |
| App Configuration (labels, dynamic refresh) | Runtime configuration | [08](08-security-and-config.md) |
| OpenTelemetry | Distributed tracing pipeline | [09](09-observability.md) |
| KQL | Monitoring/troubleshooting playground | [09](09-observability.md) |

Finish each `/docs/ai-200/*.md` file with its own "AI-200 skills covered" checklist, per phase — this table is the index, not a replacement for those.
