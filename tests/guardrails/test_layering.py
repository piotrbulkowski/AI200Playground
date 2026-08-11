"""Guardrail: src/domain must stay framework/SDK-free — pure Python + Pydantic only."""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DOMAIN_DIR = _REPO_ROOT / "src" / "domain"
_FORBIDDEN_TOP_LEVEL_MODULES = ("azure", "asyncpg", "fastapi", "starlette")


def _imported_top_level_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    return modules


def test_domain_has_no_infrastructure_or_framework_imports():
    violations = []
    for path in sorted(_DOMAIN_DIR.rglob("*.py")):
        forbidden = _imported_top_level_modules(path) & set(_FORBIDDEN_TOP_LEVEL_MODULES)
        if forbidden:
            violations.append(f"{path.relative_to(_REPO_ROOT)}: imports {sorted(forbidden)}")
    assert not violations, (
        "src/domain must not import Azure SDKs, asyncpg, or web frameworks:\n"
        + "\n".join(violations)
    )
