"""DTOs the API layer builds and hands to the application layer.

Deliberately plain — no FastAPI UploadFile, no Azure SDK types.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import IO


@dataclass(frozen=True, slots=True)
class UploadDocumentCommand:
    title: str
    category: str
    technology: str
    version: str
    author: str
    original_filename: str
    content_type: str
    content: IO[bytes]
