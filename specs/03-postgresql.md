# Phase 3 — Azure Database for PostgreSQL + pgvector

## Goal

Stand up PostgreSQL as the second mandatory store — used where the relational model earns its keep, not as a second copy of Cosmos DB — then layer pgvector on top for the relational side of semantic retrieval.

## AI-200 topics covered

Relational schema design on Azure Database for PostgreSQL, pgvector index types and tuning, connection pooling, metadata-filtered vector search, secure query construction.

## What you'll build

* A normal relational schema storing document metadata, processing information, chunk metadata, document↔chunk relationships, and audit/processing history. Use proper types (not everything-as-text) and justify primary keys, foreign keys, indexes, and cardinality in the doc.
* pgvector extension enabled; embeddings stored per chunk.
* Vector similarity search with metadata filtering — e.g. a question scoped to `technology = Azure`, `category = messaging`, `version = X` should filter *before or alongside* the vector search, not after pulling the whole table.
* Connection pooling (e.g. via PgBouncer or the platform's built-in pooling) with configurable pool size, connection timeout, command timeout, and retry behavior.

## Requirements

* Do not open a new PostgreSQL connection per request. Prove it: add a load scenario that shows the difference between pooled and unpooled connection handling (latency, connection errors under load).
* Build indexes deliberately: a vector index on the embedding column and a regular (B-tree) index on whatever metadata columns you actually filter on. Measure latency/compute with and without each.
* All SQL touching user-controllable input (e.g. a document ID from the URL, a free-text filter) must go through parameterized queries — see the exam callout below before you write a single raw SQL string.

## What the exam actually asks

* **Build order for bulk-loaded vector data: schema → bulk load data → create the vector index → then run filtered similarity queries.** Creating the vector index (IVFFlat or HNSW) *before* loading millions of embeddings is the wrong order — it slows ingestion and, for IVFFlat specifically, produces a worse index because IVFFlat's clustering step benefits from seeing representative data. Reproduce this: measure ingestion time for "index-first" vs. "bulk-load-then-index" on a batch of a few thousand synthetic embeddings.
* **pgvector has two index types with different tradeoffs — know both, don't just default to one:**
  * `IVFFlat` — faster to build, smaller memory footprint, but needs a representative data sample to cluster well (the `lists` parameter) and has lower recall than HNSW at the same speed.
  * `HNSW` — better query latency/recall, no training step, but slower and more memory-hungry to build.
  Build one experiment with each index type against the same data and compare latency and (roughly) recall so you have a real basis for the tradeoff instead of a memorized answer.
* **Combine a vector index with a plain index on your metadata filter columns.** When a query filters on `technology`/`category`/`version` *and* does vector similarity, a B-tree (or appropriate) index on the filter columns is what actually reduces the P95 latency — the vector index alone doesn't help the filtering side. Measure a filtered query with and without the metadata index.
* **Connection pooling beats raising `max_connections`.** If throughput under concurrent load is the problem, the exam wants "implement connection pooling," not "increase `max_connections`" or "increase `shared_buffers`" — those don't fix connection *churn*. Your load scenario above should demonstrate this directly.
* **SQL injection prevention = parameterized queries, not string concatenation/formatting.** Take one endpoint that accepts a user-supplied value used in a `WHERE` clause, write it first the wrong way (f-string/`.format()` into SQL), demonstrate the injection, then fix it with parameter binding (driver placeholders or an ORM's bound parameters) and show the exploit no longer works. This is a two-sided exercise — you need to see it break before the fix means anything.

## Exercises

* **PostgreSQL vector performance** (see [10-exercises-troubleshooting-roadmap.md](10-exercises-troubleshooting-roadmap.md)): semantic search is slow — diagnose the missing/misconfigured pgvector index and fix it.
* **SQL injection**: exploit then patch the vulnerable endpoint described above.

## Definition of done

* Relational schema exists with justified keys/indexes/types.
* pgvector semantic search works with metadata filtering.
* Both pgvector index types have been tried and compared at least once.
* Connection pooling is configured and its effect under load is measured.
* The SQL injection exercise has a documented before/after.
* `/docs/ai-200/postgresql.md` covers schema decisions, pgvector indexing, connection pooling, and ends with an "AI-200 skills covered" list.

Next: [04-eventing-pipeline.md](04-eventing-pipeline.md).
