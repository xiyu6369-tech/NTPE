from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from core.book_preparation import (
    BookPreparationFinding,
    BookPreparationProcessor,
)


def test_result_findings_and_nested_results_are_immutable_and_preserved(
    tmp_path: Path,
) -> None:
    text = "Chapter 1\n" + "A complete sentence. " * 80
    path = tmp_path / "book.txt"
    path.write_bytes(text.encode("utf-8"))
    result = BookPreparationProcessor().prepare(path)

    assert isinstance(result.findings, tuple)
    assert result.translation_chunks is result.chunk_plan.chunks
    assert isinstance(result.translation_chunks, tuple)
    assert result.reconstruct_text() == result.intake_result.text
    assert result.intake_result.text == text
    with pytest.raises(FrozenInstanceError):
        result.status = "blocked"
    if result.findings:
        assert isinstance(result.findings[0], BookPreparationFinding)
        with pytest.raises(FrozenInstanceError):
            result.findings[0].message = "changed"


def test_result_readiness_properties_have_strict_semantics(tmp_path: Path) -> None:
    path = tmp_path / "short.txt"
    path.write_bytes("Chapter 1\nShort.".encode("utf-8"))
    result = BookPreparationProcessor().prepare(path)
    assert result.is_ready_for_translation is (result.status == "ready")
    assert result.requires_manual_review is (result.status == "manual_review")
    assert result.is_blocked is (result.status == "blocked")
    assert not result.is_ready_for_translation
