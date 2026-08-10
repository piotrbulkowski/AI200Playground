# Phase 4 — Event-Driven Document Processing

## Goal

Wire the upload endpoint from Phase 1 into a real asynchronous pipeline: `Blob Storage → Event Grid → Azure Function → Service Bus → document processing worker`. This is the phase where "async-first" stops being a slogan and becomes something you can break and watch fail.

## AI-200 topics covered

Event Grid (subscriptions, filtering, custom events, retry/dead-letter behavior), Azure Functions (triggers, bindings, deployment), Service Bus (queues, retries, DLQ, message disposition, duplicate detection, sessions).

## What you'll build

* **Event Grid** subscription reacting to Blob Storage document create/update events.
* **Azure Function** as the event handler: it reacts to the Event Grid event and publishes a message to Service Bus. It must not contain business logic — it delegates to the application layer.
* **Service Bus queue** carrying document-processing work items. The message must carry enough to locate the document (id, blob location) — never the document content itself.
* **Document processing worker** — an independent process from the API — that receives the Service Bus message, fetches the blob, parses it, chunks it, generates embeddings, writes to Cosmos DB and PostgreSQL (Phases 2–3), and updates processing status.

## Requirements

* Do not call the worker directly from the API. The only path from upload to processing is through Event Grid → Function → Service Bus.
* Exercise duplicate processing, retries, dead-lettering, and message completion/abandonment for real — not hidden behind a framework abstraction that obscures what's actually happening on the wire.
* Add a way to deliberately fail processing (e.g. a malformed test document, or a feature flag that forces an exception) so you can watch a message land in the dead-letter queue, then add a way to reprocess it from the DLQ.
* Add a way to deliberately reject/retry an Event Grid delivery so you can observe Event Grid's retry behavior, not just Service Bus's.

## What the exam actually asks

* **Event Grid does not retry everything.** A `400` (bad request) or `413` (payload too large) response from your endpoint is treated as non-retriable — Event Grid will not keep retrying those, it moves straight to the dead-letter destination if one is configured (and drops the event if not). If a scenario says "don't lose events when the endpoint returns 400," the fix is **configuring a dead-letter destination**, not "add a retry policy" — retries won't even fire for that status code. Reproduce this: make your handler return 400 for a specific payload, confirm Event Grid doesn't retry, confirm the event shows up in your configured dead-letter destination.
* **Event Grid filtering has two tiers.** Simple subject prefix/suffix filters (`subject begins with /uploads/ai/`) cover static path-shaped conditions. When a condition needs to evaluate multiple event data fields with boolean logic (e.g. "route differently depending on a `season` field in the payload"), you need an **advanced filter**, not a subject filter and not a label — labels aren't an Event Grid filtering concept. Build one subscription using a subject prefix filter and one using an advanced filter on custom event data, so you feel the difference.
* **Endpoint validation and publisher auth are two different mechanisms.** Event Grid validates a new webhook endpoint via a validation handshake (a `validationCode` your endpoint must echo back, or the Azure AD/CloudEvents-based handshake) — that's about proving *you own the endpoint*. Separately, if you're publishing to a custom topic, a **SAS token with an expiration** is how you authenticate *as a publisher* so access isn't permanent. Don't conflate the two when documenting this.
* **Service Bus message disposition — know all four, not just "retry vs. dead-letter":**
  * `Complete` — done, remove from the queue.
  * `Abandon` — release it back immediately for redelivery (use for transient failures you want retried right away).
  * `Defer` — set it aside but keep it in the queue, retrievable later by sequence number. Use this when the message is fine but a dependency is temporarily unavailable and you want to come back to *this specific message* once it's back, without blocking the rest of the queue.
  * `Dead-letter` — move it aside for investigation; it's done being retried automatically.
  Build a scenario that uses `Defer` specifically (e.g. simulate a downstream API being down) — it's the one people forget exists and default to `Abandon` instead.
* **Preventing duplicate processing and preserving failures for investigation are two separate settings, both needed together:** Service Bus **duplicate detection** (a dedup window keyed on message ID) stops the same message from being processed twice; dead-lettering is what preserves a message that legitimately failed so you can inspect it. A scenario asking for both wants both configured — one doesn't substitute for the other.
* **Sessions are a different feature from duplicate detection** — sessions group related messages for ordered/exclusive processing; they don't dedupe. Don't reach for sessions when the actual requirement is deduplication.
* Function app settings referencing Key Vault secrets use the `@Microsoft.KeyVault(SecretUri=...)` syntax — see [08-security-and-config.md](08-security-and-config.md) for the full explanation; this Function is a good place to actually use it (e.g. for a downstream API token).

## Exercises

* **Service Bus DLQ** (see [10-exercises-troubleshooting-roadmap.md](10-exercises-troubleshooting-roadmap.md)): the worker stops processing some documents — find them in the DLQ, diagnose, reprocess.
* **Message action drill**: write a small harness that forces each of Complete/Abandon/Defer/Dead-letter and confirms the queue state matches expectations after each.

## Definition of done

* Uploading a document triggers processing without the API ever calling the worker directly.
* A deliberately-broken document ends up in the DLQ and can be reprocessed.
* Event Grid's non-retriable-status behavior and its dead-letter destination have both been demonstrated.
* Both filter tiers (prefix, advanced) exist as real subscriptions.
* `/docs/ai-200/service-bus.md` and `/docs/ai-200/event-grid.md` are written per the template, each ending with an "AI-200 skills covered" list.

Next: [05-search-and-rag.md](05-search-and-rag.md).
