from __future__ import annotations

from pathlib import Path

from core.book_chunking import BookChunkPlanner
from core.book_intake import BookIntakeProcessor
from core.book_segmentation import BookStructureSegmenter


def test_intake_segmentation_chunking_pipeline_is_offline_lossless_and_deterministic(
    tmp_path: Path, monkeypatch
) -> None:
    text = (
        "Book title\r\n\r\nChapter 1\r\n"
        + "First sentence. " * 120
        + "\r\n\r\nChapter 2\r\n"
        + "第二章內容。" * 150
    )
    source_path = tmp_path / "novel.txt"
    source_path.write_bytes(text.encode("utf-8"))
    intake = BookIntakeProcessor().process(source_path)
    segmentation = BookStructureSegmenter().segment(intake)
    before_files = {item.relative_to(tmp_path) for item in tmp_path.rglob("*")}

    def forbidden(*args, **kwargs):
        raise AssertionError("network/provider/runtime boundary must not be invoked")

    monkeypatch.setattr("socket.create_connection", forbidden)
    plans = [BookChunkPlanner().plan(segmentation) for _ in range(3)]

    assert plans[0] == plans[1] == plans[2]
    assert plans[0].reconstruct_text() == segmentation.reconstruct_text() == intake.text
    assert plans[0].source_content_fingerprint == segmentation.source_content_fingerprint
    assert all(chunk.character_count <= plans[0].maximum_chunk_size for chunk in plans[0].chunks)
    assert segmentation == BookStructureSegmenter().segment(intake)
    assert {item.relative_to(tmp_path) for item in tmp_path.rglob("*")} == before_files


def test_planner_does_not_rerun_heading_detection_or_book_intake(monkeypatch) -> None:
    segmentation = BookStructureSegmenter().segment_text(
        "Chapter 1\nText\nChapter 2\nMore", source_name="novel.txt"
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("upstream analysis must not be rerun")

    monkeypatch.setattr("core.book_segmentation.BookStructureSegmenter.segment_text", forbidden)
    monkeypatch.setattr("core.book_intake.BookIntakeProcessor.process", forbidden)
    plan = BookChunkPlanner().plan(
        segmentation,
        minimum_chunk_size=5,
        target_chunk_size=30,
        maximum_chunk_size=50,
    )
    assert plan.reconstruct_text() == segmentation.reconstruct_text()
