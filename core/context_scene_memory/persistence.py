"""Context/Scene Memory Persistence Layer.

Provides deterministic, fail-closed loading and saving of ContextMemoryStore
for per-book persistence across translation sessions.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

from .models import SCHEMA_VERSION
from .serialization import dumps_context_store, loads_context_store
from .store import ContextMemoryStore
from .validation import ContextSceneValidationError


def compute_book_identity(input_path: Path, project_name: str) -> str:
    """Compute deterministic book identity from source file and project.

    Uses source file path and project name to create a stable identifier
    that matches NTPE's deterministic source identity principles.
    """
    identity_source = f"{project_name}|{input_path.resolve()}"
    return hashlib.sha256(identity_source.encode("utf-8")).hexdigest()[:16]


def get_context_memory_file_path(output_dir: Path, book_identity: str) -> Path:
    """Get the context/scene memory persistence file path for a given book.

    Stored alongside translation output per Artifact Isolation.
    """
    return output_dir / f"context_scene_memory_{book_identity}.json"


def save_context_memory(store: ContextMemoryStore, memory_file: Path) -> dict[str, Any]:
    """Save ContextMemoryStore to disk with validation.

    Returns metadata including file hash and snapshot version.
    """
    serialized = dumps_context_store(store)
    memory_file.write_text(serialized, encoding="utf-8", newline="\n")

    file_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    return {
        "file_hash": file_hash,
        "snapshot_version": store.snapshot_version,
        "schema_version": SCHEMA_VERSION,
    }


def load_context_memory(memory_file: Path) -> ContextMemoryStore:
    """Load ContextMemoryStore from disk with fail-closed validation.

    Raises ContextSceneValidationError on any corruption or schema mismatch.
    """
    if not memory_file.exists():
        raise ContextSceneValidationError(f"context memory file not found: {memory_file}")

    content = memory_file.read_bytes()
    if not content:
        raise ContextSceneValidationError(f"context memory file is empty: {memory_file}")

    try:
        return loads_context_store(content)
    except ContextSceneValidationError:
        raise
    except (UnicodeDecodeError, Exception) as exc:
        raise ContextSceneValidationError(
            f"context memory file is not valid UTF-8 JSON: {memory_file}"
        ) from exc


def verify_context_memory_integrity(memory_file: Path, expected_hash: str) -> bool:
    """Verify context memory file matches expected hash.

    Returns True if hash matches, False otherwise.
    """
    if not memory_file.exists():
        return False
    content = memory_file.read_bytes()
    actual_hash = hashlib.sha256(content).hexdigest()
    return actual_hash == expected_hash


def load_or_create_context_memory(
    *,
    output_dir: Path,
    input_path: Path,
    project_name: str,
) -> tuple[ContextMemoryStore, dict[str, Any]]:
    """Load existing context memory or create new.

    Priority:
    1. Existing v2 context memory file
    2. Fresh ContextMemoryStore

    Returns:
        (ContextMemoryStore, load_report)
    """
    book_identity = compute_book_identity(input_path, project_name)
    memory_file = get_context_memory_file_path(output_dir, book_identity)

    load_report = {
        "book_identity": book_identity,
        "memory_file": str(memory_file),
        "source": "unknown",
    }

    if memory_file.exists():
        try:
            store = load_context_memory(memory_file)
            load_report["source"] = "v2_persisted"
            return store, load_report
        except ContextSceneValidationError as exc:
            raise ContextSceneValidationError(
                f"Failed to load existing context memory file {memory_file}: {exc}"
            ) from exc

    store = ContextMemoryStore()
    load_report["source"] = "fresh"
    return store, load_report


__all__ = [
    "compute_book_identity",
    "get_context_memory_file_path",
    "save_context_memory",
    "load_context_memory",
    "verify_context_memory_integrity",
    "load_or_create_context_memory",
]