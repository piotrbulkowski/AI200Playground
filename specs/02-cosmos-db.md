# Phase 2 — Azure Cosmos DB for NoSQL

## Goal

Make Cosmos DB the first of the two mandatory data stores, used deliberately — not as a generic document dump. By the end of this phase you should be able to explain every indexing/partitioning/consistency decision, not just have it work.

## AI-200 topics covered

Cosmos DB SDK usage, partitioning, indexing policies (including composite indexes), RU cost, consistency levels, vector search, Change Feed Processor, client-side (Always Encrypted) encryption.

## What you'll build

Store in Cosmos DB: document metadata, document chunks, embeddings, and whatever else semantic retrieval needs.

* **Partitioning.** Choose a partition key deliberately (e.g. `documentId` for chunk-level containers). Document in `/docs/ai-200/cosmos-db.md`: what the key is, why, how it affects scale-out, RU cost, and query performance — including a concrete example of a *bad* partition key choice for this domain and why it would hurt.
* **Indexing policy.** Configure it explicitly rather than accepting all Azure defaults blindly, and add a **composite index** where a query needs it (see exam callout below).
* **Vector search.** Store embeddings and support similarity search with query embedding, top-K, and metadata filtering — parameterized so search behavior can change without a code change.
* **Change Feed.** A real Change Feed Processor reacting to chunk/document writes, doing one genuine thing (e.g. updating indexing status, or invalidating a Redis cache entry from Phase 6).
* **Always Encrypted (stretch, optional but recommended for exam coverage).** Encrypt one genuinely sensitive field (e.g. author email, or an API key stored alongside a document's audit trail) client-side.

## Requirements

* Document the RU and query-performance impact of your partition key choice with a real experiment, not a guess.
* Compare a query **with** and **without** the right index — measure and record RU consumption for both.
* Run the same retrieval under at least two different consistency levels and document the observed difference in latency/staleness.
* Vector retrieval must support query embedding + top-K + metadata filtering, and expose these as configuration, not hardcoded values.

## What the exam actually asks

These are specific, easy-to-miss facts pulled from real AI-200 questions — build the experiment that proves each one to yourself, don't just memorize it:

* **Change Feed Processor state lives in a lease container.** A stateful Change Feed setup needs (a) the monitored container, (b) a separate **lease container**, and (c) a processor/host identity. The lease container is also what lets multiple processor instances split the workload and load-balance — if a question asks "how do you make Change Feed processing scale across instances," the answer is the lease container, not "strong consistency" or "autoscale throughput." Build this with more than one worker instance running against the same lease container and watch it split partitions.
* **Composite indexes are required for multi-property `ORDER BY`**, and for `ORDER BY` combined with a filter on a different property. A default/range index alone won't satisfy that query efficiently. Deliberately write a query that needs one, confirm it's slow/rejected without it, add the composite index to the indexing policy, and confirm the fix.
* **Always Encrypted setup order:** create a **Customer-Managed Key (CMK)** in Key Vault *first*, then create the **Data Encryption Key (DEK)** via the Cosmos SDK (wrapped by the CMK), then define the container's **encryption policy** referencing the DEK and the JSON paths to encrypt. If you only do the stretch exercise, do it in this order and note in your doc why the CMK has to exist before the DEK can wrap around it.
* **Shared throughput** is set at the database level (not per-container) when containers share an offer — know the difference between database-level shared throughput and container-level dedicated throughput, and configure at least one container of each kind.
* **Consistency levels:** there are five (Strong, Bounded Staleness, Session, Consistent Prefix, Eventual). The exam likes to give a scenario and ask which one(s) satisfy it — usually more than one level can work depending on what's actually required (e.g. read-your-own-writes vs. bounded lag vs. best latency). Your consistency-level experiment (above) should leave you able to argue, for a given requirement, which levels qualify and which don't — not just recite the list.

## Exercises

* **Cosmos RU optimization** (see [10-exercises-troubleshooting-roadmap.md](10-exercises-troubleshooting-roadmap.md)): a query burns too much RU — find the missing composite index and fix it.
* **Change Feed scale-out**: run 2+ processor instances against one lease container, add load, observe partition distribution.

## Definition of done

* Chunk/document data is queryable in Cosmos DB with a documented partition key rationale.
* The "query with index vs. without" and "consistency level A vs. B" experiments are runnable and their results are written up.
* Vector similarity search works end-to-end with metadata filtering.
* Change Feed Processor reacts to writes and performs a real side effect.
* `/docs/ai-200/cosmos-db.md` covers partitioning, indexing, consistency, vector search, Change Feed, and (if built) Always Encrypted, ending with an "AI-200 skills covered" list.

Next: [03-postgresql.md](03-postgresql.md).
