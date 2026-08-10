# Phase 5 — Unified Retrieval & RAG

## Goal

Make "semantic search" a first-class application concept, decoupled from which store answers it, then build the RAG pipeline on top of that abstraction.

## AI-200 topics covered

Vector search patterns across services, RAG pipeline design, metadata filtering, provider abstraction (the one place in this project that actually earns an interface per §5 of the overview).

## What you'll build

* A **retrieval provider interface** returning a unified result shape regardless of backend: `chunk_id`, `document_id`, `content`, `score`, `metadata`.
* Two concrete implementations at this point: Cosmos DB (Phase 2) and PostgreSQL + pgvector (Phase 3). A third, Redis, arrives in Phase 6 and plugs into the same interface.
* A `VECTOR_STORE` config switch (`cosmos` / `postgres` / later `redis`) selecting the active backend at runtime — no code change required to switch.
* The RAG pipeline: `question → embedding → vector retrieval → metadata filtering → context construction → LLM → answer + sources`.

## Requirements

* The RAG layer must not know or care which store produced the retrieval results — it only ever talks to the unified interface.
* Every similarity query returns a bounded, ranked top-K — never an unbounded scan. See the exam callout below for why.
* The RAG endpoint must return sources (document/chunk references) alongside the answer.
* If retrieval finds nothing sufficiently relevant, return an explicit "insufficient context" response — do not let the LLM guess an answer with no grounding.
* Write a comparison doc (`/docs/ai-200/vector-store-comparison.md`) covering query latency, filtering capability, indexing, scalability, consistency, operational complexity, cost, and what kind of data/workload each store suits best. Don't conclude one is universally better — that's not how the real tradeoff works.

## What the exam actually asks

* **Similarity queries should limit results, not paginate through them with offsets.** Vector search is a top-K nearest-neighbor operation — `LIMIT k` (or the equivalent top-K parameter) is the correct way to bound it. Offset-based pagination over a similarity-ranked result set is the wrong tool: the ranking isn't stable/meaningful the way it is for a normal sorted table scan, and it defeats the point of doing a bounded ANN search in the first place. Bake `top_k` into your unified interface as a required parameter, not an afterthought.
* Metadata filtering should narrow the candidate set for the vector search, not just post-filter the results afterward — the case study wording in Phase 3 ("technology = Azure, category = messaging, version = X, *then* semantic retrieval") is the pattern the exam expects: filter first, rank second.

## Exercises

* Force a `VECTOR_STORE` switch mid-demo (env var change + restart) and confirm the RAG endpoint behaves identically apart from the underlying latency/characteristics documented in your comparison doc.
* Ask a question with no matching documents in the corpus and confirm you get the explicit "insufficient context" response, not a hallucinated answer.

## Definition of done

* `POST /ask` (or similar) runs the full RAG pipeline and returns an answer with sources.
* Switching `VECTOR_STORE` between `cosmos` and `postgres` changes nothing about the API contract.
* The "insufficient context" path is implemented and tested.
* `/docs/ai-200/vector-store-comparison.md` and `/docs/ai-200/rag.md` exist, each ending with an "AI-200 skills covered" list.

Next: [06-caching-redis.md](06-caching-redis.md).
