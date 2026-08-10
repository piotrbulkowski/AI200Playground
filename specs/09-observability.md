# Phase 9 — OpenTelemetry, Azure Monitor, KQL

## Goal

Make the whole pipeline traceable end-to-end — API request → retrieval → database call → Service Bus operation → worker processing → AI call — with real distributed tracing, not text logs pretending to be observability. Then learn to actually query what you collected.

## AI-200 topics covered

OpenTelemetry SDK instrumentation and pipeline construction, context propagation, Azure Monitor / Application Insights, KQL.

## What you'll build

* An OpenTelemetry pipeline in the API and the worker exporting to Azure Monitor.
* Manual spans around the operations that matter (retrieval, DB calls, Service Bus send/receive, the LLM call) plus auto-instrumentation for HTTP, database, and messaging clients.
* Trace correlation that survives crossing process boundaries: API → Service Bus → worker → back through to a user-visible trace ID.
* A working set of KQL queries under `/docs/kql` against the telemetry you're actually generating.

## Requirements

* A single logical operation (e.g. one `/ask` request) must be visible as one connected trace across every component it touches, not a pile of disconnected per-component logs.
* Text logging alone does not satisfy this phase — spans and trace context are the requirement.

## What the exam actually asks

* **The canonical OpenTelemetry-to-Azure-Monitor pipeline has four distinct steps — know each one's name and its job, because the exam maps requirements to these steps individually:**
  1. **Register a global tracer provider** — construct a `TracerProvider` and call `trace.set_tracer_provider(provider)`. Skipping this means `trace.get_tracer(...)` calls elsewhere silently get a no-op tracer.
  2. **Create the Azure Monitor trace exporter** — instantiate the exporter from `azure-monitor-opentelemetry-exporter` with your Application Insights connection string.
  3. **Connect the exporter to the provider** — wrap the exporter in a **span processor** (`BatchSpanProcessor` for anything beyond a toy demo — `SimpleSpanProcessor` exports synchronously per-span and will hurt latency) and add it to the provider via `provider.add_span_processor(...)`.
  4. **Generate spans** — get a tracer via `trace.get_tracer(__name__)` and wrap real work in `tracer.start_as_current_span(...)`.
  Build this from scratch once, by hand, before reaching for a convenience wrapper — a HOTSPOT-style question will show you a code snippet missing one of these four steps and ask what breaks.

* **Auto-instrumentation is what propagates trace context across an outbound HTTP call — a manually created span does not do this by itself.** If your code makes an outbound call with `requests` (or `httpx`, etc.) without instrumenting that library (`RequestsInstrumentor().instrument()` or the equivalent), the downstream service will **not** receive the `traceparent` header, and the call will show up as a disconnected trace on the other side even though you wrapped the call in a span locally. Reproduce this deliberately: make an outbound call with the instrumentor active, then again with it removed, and diff the resulting traces in Azure Monitor.
* Minimizing correlation work **across multiple Azure Functions apps** specifically favors OpenTelemetry SDK auto-instrumentation over hand-rolled correlation IDs threaded through function bindings — if a requirement explicitly says "minimize development effort" alongside "correlate across Functions hosts," that phrasing is steering you toward auto-instrumentation, not custom header-passing.
* A cold-start-sensitive, latency-critical API service and a scale-to-zero batch worker have **different correct minimum-replica settings** even though both use KEDA — see the note in [07-containers-and-deployment.md](07-containers-and-deployment.md). Don't default every KEDA-scaled component to `minReplicaCount: 0`; a customer-facing API usually needs at least one warm replica, and this exact tension (cost vs. cold start) is a recurring exam scenario.

## KQL playground

Add `/docs/kql` with hands-on exercises against your own telemetry — each with a problem statement, expected result shape, space for your own query, and an optional reference solution:

1. Find all failed document-processing operations.
2. Find requests with latency above a threshold.
3. Compute P95 latency for the `/ask` endpoint (this needs `summarize` + `percentile()`).
4. Find traces containing a Service Bus retry.
5. Find documents that ended up in the DLQ.
6. Find the largest latency contributors in the RAG pipeline (walk the spans of one trace).
7. Find errors originating from PostgreSQL.
8. Find errors originating from Cosmos DB.

## Exercises

* **OpenTelemetry** (see [10-exercises-troubleshooting-roadmap.md](10-exercises-troubleshooting-roadmap.md)): a RAG request is slow — use a trace to find which component is actually responsible.
* Break auto-instrumentation on one outbound call on purpose, confirm the trace breaks at exactly that boundary, then fix it.

## Definition of done

* One `/ask` request produces one connected, cross-service trace visible in Azure Monitor.
* The four-step OpenTelemetry pipeline has been built by hand and is documented.
* All 8 KQL exercises are runnable against real telemetry from this project.
* `/docs/ai-200/opentelemetry.md` and `/docs/ai-200/kql.md` are written per the template, ending with "AI-200 skills covered" lists.

Next: [10-exercises-troubleshooting-roadmap.md](10-exercises-troubleshooting-roadmap.md).
