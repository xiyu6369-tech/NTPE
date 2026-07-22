from __future__ import annotations

import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from core.book_chunking import BookChunkPlanner
from core.book_intake import (
    BookIntakeManifestBuilder,
    BookIntakeProcessor,
    BookPreflightAnalyzer,
)
from core.book_preparation import (
    BookPreparationBlockedError,
    BookPreparationProcessor,
    validate_book_preparation_freeze,
)
from core.book_segmentation import BookStructureSegmenter


_ROOT = Path(__file__).resolve().parents[2]


def test_backward_compatible_explicit_and_orchestrated_pipeline(tmp_path: Path) -> None:
    text = "Chapter 1\n" + "Sentence. " * 150 + "\nChapter 2\n" + "More. " * 150
    path = tmp_path / "novel.txt"
    path.write_bytes(text.encode("utf-8"))

    intake = BookIntakeProcessor().process(path)
    preflight = BookPreflightAnalyzer().analyze(intake)
    manifest = BookIntakeManifestBuilder().build(intake, preflight)
    segmentation = BookStructureSegmenter().segment(intake, manifest=manifest)
    chunk_plan = BookChunkPlanner().plan(segmentation)
    preparation = BookPreparationProcessor().prepare_intake(intake)

    assert segmentation.reconstruct_text() == text
    assert chunk_plan.reconstruct_text() == text
    assert preparation.reconstruct_text() == text
    assert preparation.segmentation_result == segmentation
    assert preparation.chunk_plan == chunk_plan
    assert validate_book_preparation_freeze().valid


def test_freeze_pipeline_is_deterministic_offline_and_write_free(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = "Title\r\n\r\nChapter 1\r\n" + "Text. " * 500 + "\r\n"
    path = tmp_path / "novel.txt"
    path.write_bytes(text.encode("utf-8"))
    before = {item.relative_to(tmp_path) for item in tmp_path.rglob("*")}

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("network/provider/translation execution attempted")

    monkeypatch.setattr("socket.create_connection", forbidden)
    results = tuple(BookPreparationProcessor().prepare(path) for _ in range(3))
    after = {item.relative_to(tmp_path) for item in tmp_path.rglob("*")}

    assert results[0] == results[1] == results[2]
    assert results[0].reconstruct_text() == text
    assert before == after


class _BlockedIntake:
    def __init__(self, result, events):
        self.result = result
        self.events = events

    def process(self, path):
        self.events.append("intake")
        return self.result


class _ForbiddenDownstream:
    def __init__(self, events):
        self.events = events

    def analyze(self, *args, **kwargs):
        self.events.append("preflight")
        raise AssertionError("blocked Intake reached Preflight")


def test_blocked_intake_remains_fail_fast_at_freeze_boundary(tmp_path: Path) -> None:
    path = tmp_path / "book.txt"
    path.write_bytes(("Chapter 1\n" + "Text. " * 200).encode("utf-8"))
    intake = BookIntakeProcessor().process(path)
    blocked = replace(intake, status="blocked", recommended_action="reject")
    events: list[str] = []
    processor = BookPreparationProcessor(
        intake_processor=_BlockedIntake(blocked, events),
        preflight_analyzer=_ForbiddenDownstream(events),
    )
    with pytest.raises(BookPreparationBlockedError):
        processor.prepare(path)
    assert events == ["intake"]


def test_standalone_acceptance_script_passes() -> None:
    script = _ROOT / "verification" / "book_preparation" / "book_preparation_stage34_freeze_acceptance.py"
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "BOOK PREPARATION STAGE 3.4 FREEZE ACCEPTANCE: PASS" in completed.stdout
