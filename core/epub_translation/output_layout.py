"""Canonical EPUB output path layout.

EPUB translation output is source-adjacent (or root-relative for the runtime
resume/memory area). The directory segment is derived from the EPUB identifier,
which for real books is frequently a URN (``urn:uuid:...``) or another string
containing characters that are illegal in filesystem names on Windows
(``:``, ``/``, ``\\``, ``*``, ``?``, ``"``, ``<``, ``>``, ``|``).

This module provides the single canonical sanitization used by every EPUB
output path construction site so the identifier can never break directory
creation. It does not change the identifier recorded in EPUB metadata; it only
derives a filesystem-safe segment.
"""

from __future__ import annotations

import re
from pathlib import Path

# Conservative allowlist matching the repository's existing runtime naming
# convention (see core/translation_runtime/runtime_recovery.py).
_UNSAFE_SEGMENT_CHARS = re.compile(r"[^0-9A-Za-z._-]+")


def safe_output_segment(value: object, fallback: str = "unknown") -> str:
    """Return a deterministic, filesystem-safe path segment for ``value``."""
    text = str(value) if value not in (None, "") else ""
    segment = _UNSAFE_SEGMENT_CHARS.sub("_", text).strip("._-")
    return segment or fallback


def epub_output_dir(base: str | Path, identifier: object) -> Path:
    """Canonical EPUB output directory: ``<base>/output/epub_translation/<safe id>``."""
    return Path(base) / "output" / "epub_translation" / safe_output_segment(identifier)
