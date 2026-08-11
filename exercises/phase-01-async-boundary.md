# Exercise — Enforce the async boundary

**Goal:** feel the guardrail catch a real violation, not just trust that it exists.

`tests/guardrails/test_async_boundary.py` exists because Phase 1's whole point is that
`POST /documents` does metadata validation + a blob write + a metadata write, then returns.
Nothing else. The moment something starts parsing, chunking, or embedding a document inline in
that request path, you've broken the pattern every later phase (especially [Phase 4's
event-driven pipeline](../specs/04-eventing-pipeline.md)) assumes holds.

## Steps

1. Run the guardrail tests and confirm they pass:

   ```bash
   uv run pytest tests/guardrails -v
   ```

2. Open `src/application/document_service.py` and add a fake inline processing call inside
   `DocumentService.upload_document`, right after the blob upload:

   ```python
   chunk_text(document)  # pretend this exists — don't actually define it
   ```

3. Re-run the guardrail tests:

   ```bash
   uv run pytest tests/guardrails -v
   ```

   `test_document_service_upload_does_not_process_inline` should fail with a message naming the
   forbidden call (`chunk_text`), not a generic `NameError` — the guardrail catches it purely by
   inspecting the function's source via `ast`, before the code would even run.

4. Try the same thing one layer up, in `src/api/routers/documents.py::upload_document`, e.g.
   `embed_document(document)` right before the `return`. Confirm
   `test_upload_endpoint_does_not_process_inline` fails too.

5. Revert both changes and confirm the guardrail tests pass again.

## What this teaches

* The guardrail is a **syntactic heuristic** (it matches call names via `ast`, not real
  behavior) — cheap, fast, no imports needed, but it can be defeated by enough indirection.
  That's an intentional trade-off, not an oversight: see the module docstring in
  `test_async_boundary.py`.
* This is the same shape of problem AI-200 tests when it asks about Event Grid / Service Bus /
  Functions: "don't do heavy work in the request thread" is a pattern, not a one-off decision,
  and it needs to survive refactors — hence a test, not just a code review comment.
