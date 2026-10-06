"""Project-scoped Glossary backend (S12-02).

Bounded integration of a user-imported glossary into the existing canonical
``locked_dictionary`` mechanism. This module owns:

* importing text / JSON glossaries (reusing the existing runtime parsers),
* canonical normalization + deterministic content identity,
* the project-owned atomic snapshot,
* mapping an active project glossary onto canonical translation options.

It does NOT implement a second glossary engine, matching algorithm, or runtime.
No provider / network / translation is performed here.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import GlossaryRecord, ReaderProject

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_GLOSSARY_BYTES = 5 * 1024 * 1024
ALLOWED_SUFFIXES = (".txt", ".json")
HASH_HEX_LEN = 16

MODE_NONE = "none"
MODE_PROJECT_FILE = "project_file"

FORMAT_TEXT = "text"
FORMAT_JSON = "json"

SNAPSHOT_SCHEMA = "ntpe.glossary"
SNAPSHOT_VERSION = "1.0"


# ---------------------------------------------------------------------------
# Errors (bounded; deterministic, actionable, reader-safe)
# ---------------------------------------------------------------------------

class GlossaryError(Exception):
    """Base error for the project Glossary backend."""

    code = "GLOSSARY_ERROR"

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


class GlossaryValidationError(GlossaryError):
    """Import input failed validation (format / encoding / empty / oversized / unsafe)."""

    code = "GLOSSARY_VALIDATION_ERROR"


class GlossaryIntegrityError(GlossaryError):
    """Project-owned snapshot is missing, corrupt, or does not match its identity."""

    code = "GLOSSARY_INTEGRITY_ERROR"


class GlossaryPersistenceError(GlossaryError):
    """The glossary snapshot could not be persisted atomically."""

    code = "GLOSSARY_PERSISTENCE_ERROR"


# ---------------------------------------------------------------------------
# Normalization / identity
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_pairs(pairs: Any) -> dict[str, str]:
    """Strip keys/values, drop empties, coerce to ``dict[str, str]``."""
    if not isinstance(pairs, dict):
        return {}
    normalized: dict[str, str] = {}
    for source, target in pairs.items():
        if not isinstance(source, str) or not isinstance(target, str):
            continue
        src = source.strip()
        dst = target.strip()
        if src and dst:
            normalized[src] = dst
    return normalized


def merge_pairs(entries: dict[str, str], aliases: dict[str, str] | None = None) -> dict[str, str]:
    """Merge entries with aliases (aliases win on key collision)."""
    merged = dict(entries)
    if aliases:
        merged.update(aliases)
    return merged


def canonical_content_hash(entries: dict[str, str], aliases: dict[str, str] | None = None) -> str:
    """Deterministic 16-hex identity over the normalized (merged) content.

    Same normalized content -> same hash; changed content -> different hash.
    """
    merged = merge_pairs(normalize_pairs(entries), normalize_pairs(aliases or {}))
    canonical = json.dumps(
        dict(sorted(merged.items())), ensure_ascii=False, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:HASH_HEX_LEN]


def _source_file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()[:HASH_HEX_LEN]


# ---------------------------------------------------------------------------
# Import (reuses the existing canonical parsers)
# ---------------------------------------------------------------------------

def _detect_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return FORMAT_JSON
    if suffix == ".txt":
        return FORMAT_TEXT
    raise GlossaryValidationError(
        f"unsupported glossary format: {suffix or '(none)'}; expected .txt or .json"
    )


def _validate_source_path(path: str | Path) -> Path:
    file_path = Path(path)
    if not file_path.exists():
        raise GlossaryValidationError(f"glossary file not found: {file_path}")
    if not file_path.is_file():
        raise GlossaryValidationError(f"glossary path is not a file: {file_path}")
    try:
        size = file_path.stat().st_size
    except OSError as exc:
        raise GlossaryValidationError(f"cannot stat glossary file: {exc}") from exc
    if size > MAX_GLOSSARY_BYTES:
        raise GlossaryValidationError(
            f"glossary file too large: {size} bytes (max {MAX_GLOSSARY_BYTES})"
        )
    return file_path


def parse_glossary_file(path: str | Path) -> tuple[dict[str, str], str]:
    """Parse a supported glossary file into ``(entries, format)``.

    Reuses the existing runtime parsers (``load_glossary_text`` / ``load_json_pairs``)
    so there is exactly one glossary syntax interpretation in the repository.
    Malformed rows are skipped by the existing parser; a file that yields no valid
    pair after normalization is rejected.
    """
    file_path = _validate_source_path(path)
    fmt = _detect_format(file_path)

    # Strict decode check (existing parsers use errors="ignore").
    try:
        file_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise GlossaryValidationError(f"glossary encoding error: {exc}") from exc
    except OSError as exc:
        raise GlossaryValidationError(f"cannot read glossary file: {exc}") from exc

    from lts.txt_translation_runtime import load_glossary_text, load_json_pairs

    raw = load_json_pairs(file_path) if fmt == FORMAT_JSON else load_glossary_text(file_path)
    entries = normalize_pairs(raw)
    if not entries:
        raise GlossaryValidationError("glossary contains no valid source=target pairs")
    return entries, fmt


def build_record_for_file(path: str | Path) -> GlossaryRecord:
    """Build a validated GlossaryRecord (stored_path intentionally left empty)."""
    file_path = _validate_source_path(path)
    entries, fmt = parse_glossary_file(file_path)
    aliases: dict[str, str] = {}
    content_hash = canonical_content_hash(entries, aliases)
    return GlossaryRecord(
        mode=MODE_PROJECT_FILE,
        glossary_id=content_hash,
        content_hash=content_hash,
        format=fmt,
        original_path=str(file_path),
        stored_path="",
        term_count=len(entries),
        entries=entries,
        aliases=aliases,
        imported_at=_now_iso(),
        source_hash_at_import=_source_file_hash(file_path),
    )


# ---------------------------------------------------------------------------
# Snapshot payload / verification
# ---------------------------------------------------------------------------

def snapshot_payload(record: GlossaryRecord) -> dict[str, str]:
    """Canonical snapshot = pure ``{source: target}`` map (runtime-parsable).

    Only source→target pairs are stored so the existing ``load_json_pairs`` parser
    reads exactly the terminology, with no metadata keys leaking into the locked
    dictionary.
    """
    return merge_pairs(normalize_pairs(record.entries), normalize_pairs(record.aliases))


def snapshot_bytes(record: GlossaryRecord) -> bytes:
    return json.dumps(
        dict(sorted(snapshot_payload(record).items())), ensure_ascii=False, indent=2
    ).encode("utf-8")


def verify_snapshot_file(record: GlossaryRecord) -> dict[str, str]:
    """Read the project-owned snapshot and verify it against the record identity.

    Raises ``GlossaryIntegrityError`` when the snapshot is missing, unreadable, or
    its canonical identity differs from ``record.content_hash``.
    """
    if not record.stored_path:
        raise GlossaryIntegrityError("glossary snapshot path is not recorded")
    snapshot_path = Path(record.stored_path)
    if not snapshot_path.is_file():
        raise GlossaryIntegrityError(f"glossary snapshot missing: {snapshot_path}")
    try:
        data = json.loads(snapshot_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise GlossaryIntegrityError(f"glossary snapshot unreadable: {exc}") from exc
    if not isinstance(data, dict):
        raise GlossaryIntegrityError("glossary snapshot has an unexpected shape")

    pairs = {str(k): str(v) for k, v in data.items() if isinstance(k, str) and isinstance(v, str)}
    actual = canonical_content_hash(pairs, {})
    if record.content_hash and actual != record.content_hash:
        raise GlossaryIntegrityError(
            f"glossary snapshot identity mismatch: expected {record.content_hash}, got {actual}"
        )
    return pairs


# ---------------------------------------------------------------------------
# Activeness / canonical option binding
# ---------------------------------------------------------------------------

def active_record(project: ReaderProject) -> GlossaryRecord | None:
    record = project.glossary
    if record is not None and record.mode == MODE_PROJECT_FILE:
        return record
    return None


def is_active(project: ReaderProject) -> bool:
    return active_record(project) is not None


def active_content_hash(project: ReaderProject) -> str | None:
    record = active_record(project)
    return record.content_hash if record is not None else None


def resolve_active_glossary(project: ReaderProject) -> dict[str, str]:
    """Return the verified active glossary pairs, or ``{}`` when none is attached."""
    record = active_record(project)
    if record is None:
        return {}
    return verify_snapshot_file(record)


def glossary_option_path(project: ReaderProject) -> Path | None:
    """Return the project-owned snapshot path for canonical options, or ``None``.

    Verifies snapshot integrity when a glossary is active.
    """
    record = active_record(project)
    if record is None:
        return None
    verify_snapshot_file(record)
    return Path(record.stored_path)


def apply_glossary_to_options(project: ReaderProject, options: Any) -> Any:
    """Return canonical translation options bound to the active project glossary.

    Canonical options are frozen dataclasses, so this returns a new instance
    (``dataclasses.replace``) with ``glossary_path`` set (and ``glossary_hash`` when
    the options type supports it). Feature-off (no glossary) returns the options
    unchanged, so existing behaviour is preserved.
    """
    record = active_record(project)
    if record is None:
        return options
    verify_snapshot_file(record)
    path = Path(record.stored_path)
    if hasattr(options, "glossary_hash"):
        return dataclasses.replace(options, glossary_path=path, glossary_hash=record.content_hash)
    return dataclasses.replace(options, glossary_path=path)


# ---------------------------------------------------------------------------
# Persistence helpers (delegate atomic write to the project store)
# ---------------------------------------------------------------------------

def persist_snapshot(store: Any, project_id: str, record: GlossaryRecord) -> GlossaryRecord:
    """Write the project-owned snapshot and return the record with ``stored_path`` set."""
    try:
        snapshot_path = store.write_glossary_snapshot(project_id, record.content_hash, snapshot_payload(record))
    except GlossaryError:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise GlossaryPersistenceError(f"failed to persist glossary snapshot: {exc}") from exc
    return dataclasses.replace(record, stored_path=str(snapshot_path))
