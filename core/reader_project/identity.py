"""Source identity for Reader Projects (S9-02, S9 §5).

Reuses the canonical identity formulas already used by the runtime so that a
Project's recorded identity is directly comparable with runtime-produced data:

* TXT  : ``sha256(file_bytes)[:16]``  (same as
  ``CanonicalBookIntakeAdapter.process_path`` → ``SourceIdentity.source_hash``)
* EPUB : ``sha256(file_bytes)``       (same as
  ``EpubExtractionBoundary.extract`` → ``EpubExtractionResult.original_hash``)

No new hashing scheme is introduced.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from .models import SourceRecord


TXT_IDENTITY_KIND = "txt_sha256_16"
EPUB_IDENTITY_KIND = "epub_sha256"


@dataclass(frozen=True)
class SourceIdentity:
    path: str
    format: str
    identity_kind: str
    hash: str
    file_size: int
    modified_time: float

    def to_source_record(
        self,
        title: str = "",
        language: str = "ko",
        encoding: str | None = None,
    ) -> SourceRecord:
        return SourceRecord(
            path=self.path,
            format=self.format,
            identity_kind=self.identity_kind,
            hash=self.hash,
            file_size=self.file_size,
            modified_time=self.modified_time,
            title=title,
            language=language,
            encoding=encoding,
        )


def normalize_format(fmt: str) -> str:
    value = str(fmt or "").strip().lower().lstrip(".")
    if value not in ("txt", "epub"):
        raise ValueError(f"unsupported source format: {fmt!r}")
    return value


def compute_source_identity(path: str | Path, *, format: str | None = None) -> SourceIdentity:
    """Compute canonical identity for a source file.

    ``format`` is inferred from the suffix when omitted. Raises
    ``FileNotFoundError`` if the path does not exist.
    """
    source_path = Path(path)
    resolved = source_path.resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"source file not found: {source_path}")

    fmt = normalize_format(format if format is not None else resolved.suffix)
    stat = resolved.stat()
    content = resolved.read_bytes()

    if fmt == "epub":
        digest = hashlib.sha256(content).hexdigest()
        identity_kind = EPUB_IDENTITY_KIND
    else:
        digest = hashlib.sha256(content).hexdigest()[:16]
        identity_kind = TXT_IDENTITY_KIND

    return SourceIdentity(
        path=str(resolved),
        format=fmt,
        identity_kind=identity_kind,
        hash=digest,
        file_size=stat.st_size,
        modified_time=stat.st_mtime,
    )


def source_matches(record: SourceRecord) -> bool:
    """Return True when the current file still matches the recorded identity.

    Cheap check first (size + mtime); only re-hash when those differ.
    """
    if not record.path:
        return False
    path = Path(record.path)
    if not path.exists():
        return False
    try:
        stat = path.stat()
    except OSError:
        return False

    if (
        int(record.file_size) == stat.st_size
        and abs(float(record.modified_time) - stat.st_mtime) < 1e-6
    ):
        return True

    try:
        current = compute_source_identity(path, format=record.format)
    except (OSError, ValueError):
        return False
    return current.identity_kind == record.identity_kind and current.hash == record.hash


def source_changed(record: SourceRecord) -> bool:
    return not source_matches(record)
