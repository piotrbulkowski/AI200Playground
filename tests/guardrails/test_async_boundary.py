"""Guardrail: the upload code path must never do inline processing (parse/chunk/embed/LLM calls).

This is a syntactic heuristic on call *targets*, not a soundness guarantee — a call routed
through an unrelated indirection could still slip past it. Its purpose is to fail loudly the
day someone adds an inline chunk(...)/embed(...)/llm(...)-style call to the upload path instead
of routing it through Phase 4's event-driven pipeline. See exercises/phase-01-async-boundary.md
for a hands-on drill that intentionally breaks this test.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
from collections.abc import Callable

from src.api.routers.documents import upload_document
from src.application.document_service import DocumentService

_FORBIDDEN_SUBSTRINGS = (
    "chunk",
    "embed",
    "llm",
    "parse_document",
    "process_document",
    "vectorize",
)
_FORBIDDEN_MODULE_PREFIXES = ("src.ai", "src.workers", "ai.", "workers.")


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_dotted_name(node.value)}.{node.attr}"
    return ""


def _call_targets(func: Callable) -> list[str]:
    source = textwrap.dedent(inspect.getsource(func))
    tree = ast.parse(source)
    return [
        _dotted_name(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)
    ]


def _assert_no_inline_processing(func: Callable) -> None:
    for target in _call_targets(func):
        lowered = target.lower()
        assert not any(bad in lowered for bad in _FORBIDDEN_SUBSTRINGS), (
            f"{func.__qualname__} calls {target!r} — inline processing must go through the "
            "event-driven pipeline (Phase 4), not the synchronous upload path."
        )
        assert not lowered.startswith(_FORBIDDEN_MODULE_PREFIXES), (
            f"{func.__qualname__} calls {target!r} directly — src.ai/src.workers must not be "
            "invoked from the upload path."
        )


def test_upload_endpoint_does_not_process_inline():
    _assert_no_inline_processing(upload_document)


def test_document_service_upload_does_not_process_inline():
    _assert_no_inline_processing(DocumentService.upload_document)
