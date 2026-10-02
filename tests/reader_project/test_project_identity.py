"""S9-02 source-identity tests.

Hermetic: no provider, no network, no real translation.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.reader_project.identity import (
    EPUB_IDENTITY_KIND,
    TXT_IDENTITY_KIND,
    compute_source_identity,
    normalize_format,
    source_changed,
    source_matches,
)


def _write(path: Path, content: bytes) -> Path:
    path.write_bytes(content)
    return path


def test_txt_identity_matches_canonical_formula(tmp_path):
    source = _write(tmp_path / "novel.txt", "그는 문을 열었다.\n".encode("utf-8"))
    identity = compute_source_identity(source)
    assert identity.format == "txt"
    assert identity.identity_kind == TXT_IDENTITY_KIND
    assert identity.hash == hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    assert len(identity.hash) == 16
    assert identity.path == str(source.resolve())
    assert identity.file_size == source.stat().st_size


def test_epub_identity_matches_canonical_formula(tmp_path):
    source = _write(tmp_path / "book.epub", b"PK\x03\x04fake-epub-bytes")
    identity = compute_source_identity(source)
    assert identity.format == "epub"
    assert identity.identity_kind == EPUB_IDENTITY_KIND
    assert identity.hash == hashlib.sha256(source.read_bytes()).hexdigest()
    assert len(identity.hash) == 64


def test_format_override_and_inference(tmp_path):
    source = _write(tmp_path / "data.bin", b"abc")
    assert compute_source_identity(source, format="txt").identity_kind == TXT_IDENTITY_KIND
    assert compute_source_identity(source, format=".EPUB").identity_kind == EPUB_IDENTITY_KIND
    with pytest.raises(ValueError):
        normalize_format("pdf")


def test_missing_source_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        compute_source_identity(tmp_path / "missing.txt")


def test_source_matches_and_detects_change(tmp_path):
    source = _write(tmp_path / "novel.txt", b"original content")
    record = compute_source_identity(source).to_source_record()
    assert source_matches(record)
    assert not source_changed(record)

    source.write_bytes(b"different content")
    assert source_changed(record)
    assert not source_matches(record)


def test_source_matches_false_when_missing(tmp_path):
    source = _write(tmp_path / "novel.txt", b"content")
    record = compute_source_identity(source).to_source_record()
    source.unlink()
    assert not source_matches(record)
    assert source_changed(record)
