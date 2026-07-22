from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from core.book_intake import (
    BookIntakeManifestBuilder,
    BookIntakeProcessor,
    BookPreflightAnalyzer,
)
from core.book_segmentation import BookStructureSegmenter
from core.book_segmentation.errors import SourceFingerprintMismatchError


def _intake(tmp_path: Path, text: str):
    path = tmp_path / "novel.txt"
    path.write_bytes(text.encode("utf-8"))
    return BookIntakeProcessor().process(path)


def test_intake_result_maps_exactly_without_mutation_or_external_side_effects(tmp_path: Path, monkeypatch) -> None:
    text = "書名\r\n\r\n第一章\r\n內容 e\u0301\r\n第二章\r\n結尾"
    intake = _intake(tmp_path, text)
    before_intake = intake
    before_files = {item.relative_to(tmp_path) for item in tmp_path.rglob("*")}

    def forbidden(*args, **kwargs):
        raise AssertionError("external/runtime boundary must not be invoked")

    monkeypatch.setattr("socket.create_connection", forbidden)
    results = [BookStructureSegmenter().segment(intake) for _ in range(3)]

    assert results[0] == results[1] == results[2]
    assert results[0].reconstruct_text() == intake.text == text
    assert results[0].source_name == "novel.txt"
    assert results[0].source_content_fingerprint == hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert intake == before_intake
    assert {item.relative_to(tmp_path) for item in tmp_path.rglob("*")} == before_files


def test_matching_manifest_is_validated_without_becoming_a_text_source(tmp_path: Path) -> None:
    intake = _intake(tmp_path, "Chapter 1\nText\nChapter 2\nMore")
    preflight = BookPreflightAnalyzer().analyze(intake)
    manifest = BookIntakeManifestBuilder().build(intake, preflight)
    result = BookStructureSegmenter().segment(intake, manifest=manifest)
    assert result.reconstruct_text() == intake.text
    assert result.source_content_fingerprint == manifest.content_fingerprint


def test_mismatched_manifest_fingerprint_is_rejected(tmp_path: Path) -> None:
    first = _intake(tmp_path, "Chapter 1\nText")
    preflight = BookPreflightAnalyzer().analyze(first)
    manifest = BookIntakeManifestBuilder().build(first, preflight)
    second = _intake(tmp_path, "Chapter 2\nDifferent")
    with pytest.raises(SourceFingerprintMismatchError):
        BookStructureSegmenter().segment(second, manifest=manifest)
