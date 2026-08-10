# Phase 6 — Azure Managed Redis

## Goal

Use Redis in two genuinely different roles: a cache in front of RAG, and a standalone vector index. They're unrelated exam topics that happen to share infrastructure — treat them as two separate mini-projects.

## AI-200 topics covered

Cache-aside pattern, cache invalidation strategy, Redis eviction policies, Redis as a vector search backend.

## What you'll build

### Scenario A — cache-aside for RAG

* Cache RAG answers and/or retrieval results, keyed by everything that affects the result (question text/embedding, `VECTOR_STORE`, top-K, filters — get the cache key wrong and you'll serve stale or wrong answers for a *different* query).
* TTL of 10 minutes on cache entries.
* A **reactive invalidation path**: when a document's metadata changes, the related cache entries must be actively deleted, not just left to expire. Wire this up to the Cosmos DB Change Feed from Phase 2 (or an equivalent Postgres-side trigger/outbox) — a metadata update should trigger deletion of the cache keys derived from that document, not wait out the TTL.
* An eviction policy appropriate for "keep frequently-accessed embeddings/answers in memory, let the rest go" (see exam callout).
* A cache-statistics endpoint (hit/miss counts, current eviction policy) — this is the "administration/learning" surface called out in the overview's API list.

### Scenario B — Redis as a vector index

* A second retrieval provider implementing the same unified interface from Phase 5, backed by Redis's vector search capability.
* Doesn't need to be the default backend, but must be swappable in via `VECTOR_STORE=redis` and produce the same unified result shape.

## Requirements

* Cover cache hit, miss, expiration, and explicit invalidation as distinct, demonstrable states — don't just implement "get-or-set" and call it done.
* The Redis vector index must support the same top-K + metadata-filtering contract as the other two backends.

## What the exam actually asks

* **Cache-aside consistency needs two things together: a reactive invalidation trigger *and* deleting the specific related keys** — TTL alone doesn't satisfy a "must reflect current data" requirement, and sliding expiration doesn't either (it extends life on *access*, which is the opposite of what you want when the underlying data changed). When the scenario says entries must be invalidated reactively on a metadata update, the answer is: react to the change event, then delete the related cache key(s). This is exactly the Change Feed → cache invalidation wiring above — build it for real, don't fake it with a short TTL and call it "close enough."
* **Eviction policy: `allkeys-lru` is what keeps "frequently accessed" data in memory under a size limit.** It evicts least-recently-used keys across the whole keyspace once memory is full. Contrast it with `volatile-ttl` (evicts among keys *that have a TTL*, preferring the ones closest to expiring — different goal, and blind to keys without a TTL) and note that `EXPIRE` isn't an eviction policy at all, it just sets a TTL on one key. Configure `allkeys-lru`, put more embeddings in than your `maxmemory` allows, and confirm the least-used ones get evicted first.
* **Redis vector search: pick the algorithm for the workload, don't default to one.** RediSearch's vector field supports `FLAT` (exact/brute-force — fine for small datasets, exact results) and `HNSW` (approximate nearest neighbor — the right choice when the requirement is *low-latency ANN search at large scale*, which is exactly how these exam scenarios are usually phrased). If a question describes large-scale, low-latency, approximate similarity search, that phrasing is pointing at `HNSW`, not `FLAT`. Configure both once so you've seen the tradeoff, but build Scenario B on `HNSW`.

## Exercises

* Trigger a metadata update and confirm the *specific* affected cache keys disappear immediately, without waiting for the 10-minute TTL.
* Fill Redis past `maxmemory` under `allkeys-lru` and confirm the least-recently-used entries are the ones evicted.
* Run the same semantic query against the Postgres, Cosmos, and Redis retrieval providers and confirm identical result shape (values may differ, structure must not).

## Definition of done

* Cache hit/miss/expiration/invalidation are all independently demonstrable.
* Reactive invalidation is wired to a real upstream change event, not a shortened TTL.
* `allkeys-lru` behavior has been observed under memory pressure.
* Redis vector search returns unified-shape results and is selectable via `VECTOR_STORE=redis`.
* `/docs/ai-200/redis.md` written per the template, ending with an "AI-200 skills covered" list.

Next: [07-containers-and-deployment.md](07-containers-and-deployment.md).
