from __future__ import annotations

import pytest
from typing import Any

from core.translation_release.reader_structure.models import ChapterBoundary, ReaderChapterMap
from core.translation_release.reader_structure.chapter_mapper import build_reader_chapter_map


def _make_record(
    chapter_id: str | None = None,
    scene_id: str | None = None,
    boundary_type: str = "chapter_transition",
    source_chunk_text: str = "",
) -> dict:
    """Create a production-shaped chunk record.

    Production structure:
    - chapter_id is inside boundary object
    - scene_id is at BOTH context_state top level AND inside boundary
    """
    boundary: dict[str, Any] = {"type": boundary_type}
    if chapter_id:
        boundary["chapter_id"] = chapter_id
    if scene_id:
        boundary["scene_id"] = scene_id
    ctx: dict[str, Any] = {"boundary": boundary}
    if scene_id:
        ctx["scene_id"] = scene_id
    record: dict[str, Any] = {"metadata": {"context_state": ctx}}
    if source_chunk_text:
        record["source"] = {"chunk_text": source_chunk_text}
    return record


def _assemble(translated_chunks: list[str]) -> str:
    """Replicate RM-8.3 assembly: join with \n\n, strip, add trailing \n."""
    return "\n\n".join(translated_chunks).strip() + "\n"


class TestImmutableModels:
    """Test 1 — Immutable model verification."""

    def test_chapter_boundary_immutable(self):
        """ChapterBoundary should be immutable (frozen dataclass)."""
        cb = ChapterBoundary(
            chapter_id="ch1",
            chapter_order=0,
            chapter_title="第1章",
            start_position=0,
            end_position=100,
            scene_ids=("scene1", "scene2"),
        )
        with pytest.raises(AttributeError):
            cb.chapter_id = "ch2"  # type: ignore
        with pytest.raises(AttributeError):
            cb.start_position = 50  # type: ignore

    def test_reader_chapter_map_immutable(self):
        """ReaderChapterMap should be immutable (frozen dataclass)."""
        cb = ChapterBoundary(
            chapter_id="ch1",
            chapter_order=0,
            chapter_title="第1章",
            start_position=0,
            end_position=100,
            scene_ids=("scene1",),
        )
        rcm = ReaderChapterMap(chapters=(cb,))
        with pytest.raises(AttributeError):
            rcm.chapters = ()  # type: ignore


class TestDeterministicMapping:
    """Test 2 — Deterministic mapping."""

    def test_same_input_produces_same_output(self):
        """Identical input must produce identical mapping."""
        translated_chunks = ["第1章 内容1", "第2章 内容2"]
        txt_body = _assemble(translated_chunks)
        chunk_records = [
            _make_record(chapter_id="ch1", scene_id="s1", source_chunk_text="第1章 内容1"),
            _make_record(chapter_id="ch2", scene_id="s2", source_chunk_text="第2章 内容2"),
        ]

        map_a = build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)
        map_b = build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)

        assert map_a == map_b


class TestCorrectChapterOrder:
    """Test 3 — Correct chapter order (first appearance order)."""

    def test_chapter_order_by_first_appearance(self):
        """Chapter order must follow first appearance in TXT."""
        translated_chunks = ["第3章 第三", "第1章 第一", "第2章 第二"]
        txt_body = _assemble(translated_chunks)
        chunk_records = [
            _make_record(chapter_id="ch3", scene_id="s1", source_chunk_text="第3章 第三"),
            _make_record(chapter_id="ch1", scene_id="s2", source_chunk_text="第1章 第一"),
            _make_record(chapter_id="ch2", scene_id="s3", source_chunk_text="第2章 第二"),
        ]

        result = build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)
        assert result.chapters[0].chapter_order == 0
        assert result.chapters[0].chapter_id == "ch3"
        assert result.chapters[1].chapter_order == 1
        assert result.chapters[1].chapter_id == "ch1"
        assert result.chapters[2].chapter_order == 2
        assert result.chapters[2].chapter_id == "ch2"


class TestCorrectChapterIdentity:
    """Test 4 — RM-8.2 chapter_id takes priority over marker."""

    def test_rm82_provenance_priority(self):
        """RM-8.2 chapter_id must take priority over explicit marker."""
        translated_chunks = ["第99章 内容", "第2章 内容"]
        txt_body = _assemble(translated_chunks)
        chunk_records = [
            _make_record(chapter_id="real_ch1", scene_id="s1", source_chunk_text="第99章 内容"),
            _make_record(chapter_id="real_ch2", scene_id="s2", source_chunk_text="第2章 内容"),
        ]

        result = build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)
        assert result.chapters[0].chapter_id == "real_ch1"
        assert result.chapters[1].chapter_id == "real_ch2"
        assert result.chapters[0].chapter_title == "第99章"
        assert result.chapters[1].chapter_title == "第2章"


class TestExplicitMarkerFallback:
    """Test 5 — Explicit marker fallback when no provenance."""

    def test_explicit_marker_fallback(self):
        """When no RM-8.2 provenance, explicit marker should work."""
        translated_chunks = ["第1章 第一", "第2章 第二"]
        txt_body = _assemble(translated_chunks)
        chunk_records = [
            _make_record(scene_id="s1", source_chunk_text="第1章 第一"),
            _make_record(scene_id="s2", source_chunk_text="第2章 第二"),
        ]

        result = build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)
        assert result.chapters[0].chapter_id == "第1章"
        assert result.chapters[0].chapter_title == "第1章"
        assert result.chapters[1].chapter_id == "第2章"
        assert result.chapters[1].chapter_title == "第2章"

    def test_chapter_pattern_variants(self):
        """Test various chapter marker patterns."""
        translated_chunks = ["Chapter 1 First", "CHAPTER 2 Second", "第 3 章 Third"]
        txt_body = _assemble(translated_chunks)
        chunk_records = [
            _make_record(scene_id="s1", source_chunk_text="Chapter 1 First"),
            _make_record(scene_id="s2", source_chunk_text="CHAPTER 2 Second"),
            _make_record(scene_id="s3", source_chunk_text="第 3 章 Third"),
        ]

        result = build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)
        assert result.chapters[0].chapter_title == "Chapter1"
        assert result.chapters[1].chapter_title == "CHAPTER2"
        assert result.chapters[2].chapter_title == "第3章"


class TestNoHeuristicInference:
    """Test 6 — No heuristic inference when no provenance and no marker."""

    def test_deterministic_fallback_no_provenance_no_marker(self):
        """When no provenance and no marker, use deterministic fallback."""
        translated_chunks = ["内容1", "内容2"]
        txt_body = _assemble(translated_chunks)
        chunk_records = [
            _make_record(scene_id="s1", source_chunk_text="内容1"),
            _make_record(scene_id="s2", source_chunk_text="内容2"),
        ]

        result = build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)
        assert result.chapters[0].chapter_id == "chapter_0"
        assert result.chapters[0].chapter_title == "第0章"
        assert result.chapters[1].chapter_id == "chapter_1"
        assert result.chapters[1].chapter_title == "第1章"


class TestPositionValidity:
    """Test 7 — Position validity."""

    def test_positions_within_bounds(self):
        """All positions must be within txt_body bounds."""
        translated_chunks = ["第1章 内容"]
        txt_body = _assemble(translated_chunks)
        chunk_records = [
            _make_record(chapter_id="ch1", scene_id="s1", source_chunk_text="第1章 内容"),
        ]

        result = build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)
        for chapter in result.chapters:
            assert 0 <= chapter.start_position < chapter.end_position <= len(txt_body)


class TestNoOverlap:
    """Test 8 — No overlap."""

    def test_adjacent_chapters_no_overlap(self):
        """Adjacent chapters must not overlap."""
        translated_chunks = ["第1章 一", "第2章 二"]
        txt_body = _assemble(translated_chunks)
        chunk_records = [
            _make_record(chapter_id="ch1", scene_id="s1", source_chunk_text="第1章 一"),
            _make_record(chapter_id="ch2", scene_id="s2", source_chunk_text="第2章 二"),
        ]

        result = build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)
        for i in range(len(result.chapters) - 1):
            assert result.chapters[i].end_position == result.chapters[i + 1].start_position


class TestNoGap:
    """Test 9 — No gap."""

    def test_no_gap_between_chapters(self):
        """No gap allowed between chapters."""
        translated_chunks = ["第1章 一", "第2章 二"]
        txt_body = _assemble(translated_chunks)
        chunk_records = [
            _make_record(chapter_id="ch1", scene_id="s1", source_chunk_text="第1章 一"),
            _make_record(chapter_id="ch2", scene_id="s2", source_chunk_text="第2章 二"),
        ]

        result = build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)
        for i in range(len(result.chapters) - 1):
            assert result.chapters[i].end_position == result.chapters[i + 1].start_position


class TestFullContentReconstruction:
    """Test 10 — Full content reconstruction (core test)."""

    def test_reconstructed_equals_original(self):
        """Reconstructed text must equal original txt_body exactly."""
        translated_chunks = ["第1章 第一段内容", "第2章 第二段内容", "第3章 第三段内容"]
        txt_body = _assemble(translated_chunks)
        chunk_records = [
            _make_record(chapter_id="ch1", scene_id="s1", source_chunk_text="第1章 第一段内容"),
            _make_record(chapter_id="ch2", scene_id="s2", source_chunk_text="第2章 第二段内容"),
            _make_record(chapter_id="ch3", scene_id="s3", source_chunk_text="第3章 第三段内容"),
        ]

        result = build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)
        reconstructed = "".join(
            txt_body[c.start_position:c.end_position]
            for c in result.chapters
        )
        assert reconstructed == txt_body

    def test_multiline_chapters(self):
        """Test with multi-line chapter content."""
        translated_chunks = ["第1章\n第一行\n第二行", "第2章\n第三行\n第四行"]
        txt_body = _assemble(translated_chunks)
        chunk_records = [
            _make_record(chapter_id="ch1", scene_id="s1", source_chunk_text="第1章\n第一行\n第二行"),
            _make_record(chapter_id="ch2", scene_id="s2", source_chunk_text="第2章\n第三行\n第四行"),
        ]

        result = build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)
        reconstructed = "".join(
            txt_body[c.start_position:c.end_position]
            for c in result.chapters
        )
        assert reconstructed == txt_body


class TestEmptyMalformedInput:
    """Test 11 — Empty / malformed input."""

    def test_empty_txt_and_empty_records(self):
        """Empty txt_body with empty records should return empty map."""
        result = build_reader_chapter_map(txt_body="", translated_chunks=[], chunk_records=[])
        assert result.chapters == ()

    def test_empty_txt_with_records_raises(self):
        """Empty txt_body with records should raise."""
        translated_chunks = ["内容"]
        txt_body = _assemble(translated_chunks)
        chunk_records = [
            _make_record(chapter_id="ch1", scene_id="s1", source_chunk_text="内容"),
        ]
        with pytest.raises(ValueError, match="empty txt_body"):
            build_reader_chapter_map(txt_body="", translated_chunks=translated_chunks, chunk_records=chunk_records)

    def test_non_empty_txt_without_records_raises(self):
        """Non-empty txt_body without records should raise."""
        translated_chunks = ["内容"]
        txt_body = _assemble(translated_chunks)
        with pytest.raises(ValueError, match="no chunk records"):
            build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=[])

    def test_mismatched_chunks_and_records_raises(self):
        """Mismatched translated_chunks and chunk_records lengths should raise."""
        translated_chunks = ["内容1", "内容2"]
        txt_body = _assemble(translated_chunks)
        chunk_records = [
            _make_record(chapter_id="ch1", scene_id="s1", source_chunk_text="内容1"),
        ]
        with pytest.raises(ValueError, match="must match"):
            build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)

    def test_conflicting_chapter_ids_merged(self):
        """Same chapter_id across records should merge into single chapter."""
        translated_chunks = ["第1章 内容1", "第1章 内容2"]
        txt_body = _assemble(translated_chunks)
        chunk_records = [
            _make_record(chapter_id="ch1", scene_id="s1", source_chunk_text="第1章 内容1"),
            _make_record(chapter_id="ch1", scene_id="s2", source_chunk_text="第1章 内容2"),
        ]

        result = build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)
        assert len(result.chapters) == 1
        assert result.chapters[0].chapter_id == "ch1"


class TestTxtImmutability:
    """Test 12 — TXT immutability."""

    def test_txt_body_unchanged_after_mapping(self):
        """txt_body must remain unchanged after mapping."""
        translated_chunks = ["第1章 内容1", "第2章 内容2"]
        txt_body = _assemble(translated_chunks)
        original = txt_body
        chunk_records = [
            _make_record(chapter_id="ch1", scene_id="s1", source_chunk_text="第1章 内容1"),
            _make_record(chapter_id="ch2", scene_id="s2", source_chunk_text="第2章 内容2"),
        ]

        build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)
        assert txt_body == original


class TestSceneMapping:
    """Additional test — Scene IDs mapping."""

    def test_scene_ids_preserved_in_order(self):
        """Scene IDs must be preserved in TXT order, deduplicated."""
        translated_chunks = ["第1章\n场景1\n场景2\n场景1", "第2章\n场景3"]
        txt_body = _assemble(translated_chunks)
        chunk_records = [
            _make_record(chapter_id="ch1", scene_id="s1", source_chunk_text="第1章\n场景1\n场景2\n场景1"),
            _make_record(chapter_id="ch2", scene_id="s2", source_chunk_text="第2章\n场景3"),
        ]

        result = build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)
        assert result.chapters[0].scene_ids == ("s1",)
        assert result.chapters[1].scene_ids == ("s2",)


class TestFirstAndLastChapterPositions:
    """Test first chapter starts at 0, last ends at len(txt_body)."""

    def test_first_chapter_starts_at_zero(self):
        """First chapter must start at position 0."""
        translated_chunks = ["第1章 内容"]
        txt_body = _assemble(translated_chunks)
        chunk_records = [
            _make_record(chapter_id="ch1", scene_id="s1", source_chunk_text="第1章 内容"),
        ]

        result = build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)
        assert result.chapters[0].start_position == 0

    def test_last_chapter_ends_at_txt_body_length(self):
        """Last chapter must end at len(txt_body)."""
        translated_chunks = ["第1章 内容"]
        txt_body = _assemble(translated_chunks)
        chunk_records = [
            _make_record(chapter_id="ch1", scene_id="s1", source_chunk_text="第1章 内容"),
        ]

        result = build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)
        assert result.chapters[-1].end_position == len(txt_body)


class TestProductionShapedInput:
    """Regression test — Production-shaped chunk record structure."""

    def test_production_chunk_record_structure(self):
        """Test with actual production-shaped chunk records (no translated_text field)."""
        translated_chunks = [
            "第1章 开始\n第一场景内容",
            "第二场景继续\n第2章 转折\n第二场景内容",
        ]
        txt_body = _assemble(translated_chunks)

        # Production-shaped records: no translated_text, only metadata.context_state
        chunk_records = [
            {
                "metadata": {
                    "context_state": {
                        "scene_id": "scene_1",
                        "scene_version": 1,
                        "boundary": {
                            "type": "chapter_transition",
                            "chapter_id": "ch1",
                        },
                    }
                },
                "source": {"chunk_text": "第1章 开始\n第一场景内容"},
                "qa": {"passed": True, "metrics": {"literary_quality_passed": True}},
                "status": "success",
                "chunk_index": 1,
                "chunk_total": 2,
            },
            {
                "metadata": {
                    "context_state": {
                        "scene_id": "scene_2",
                        "scene_version": 1,
                        "boundary": {
                            "type": "chapter_transition",
                            "chapter_id": "ch2",
                        },
                    }
                },
                "source": {"chunk_text": "第二场景继续\n第2章 转折\n第二场景内容"},
                "qa": {"passed": True, "metrics": {"literary_quality_passed": True}},
                "status": "success",
                "chunk_index": 2,
                "chunk_total": 2,
            },
        ]

        result = build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)

        assert len(result.chapters) == 2
        assert result.chapters[0].chapter_id == "ch1"
        assert result.chapters[1].chapter_id == "ch2"
        assert result.chapters[0].scene_ids == ("scene_1",)
        assert result.chapters[1].scene_ids == ("scene_2",)

        # Verify content preservation
        reconstructed = "".join(
            txt_body[c.start_position:c.end_position]
            for c in result.chapters
        )
        assert reconstructed == txt_body

    def test_production_with_scene_transitions(self):
        """Test with scene_transition boundaries (not just chapter_transition).

        Uses production structure: chapter_id inside boundary object.
        """
        translated_chunks = [
            "第1章 场景1",
            "场景2",
            "第2章 场景3",
        ]
        txt_body = _assemble(translated_chunks)

        chunk_records = [
            {
                "metadata": {
                    "context_state": {
                        "scene_id": "scene_1",
                        "scene_version": 1,
                        "boundary": {
                            "type": "chapter_transition",
                            "chapter_id": "ch1",
                            "scene_id": "scene_1",
                            "confidence": 0.95,
                        },
                    }
                },
                "source": {"chunk_text": "第1章 场景1"},
            },
            {
                "metadata": {
                    "context_state": {
                        "scene_id": "scene_2",
                        "scene_version": 1,
                        "boundary": {
                            "type": "scene_transition",
                            "chapter_id": "ch1",
                            "scene_id": "scene_2",
                            "confidence": 0.9,
                        },
                    }
                },
                "source": {"chunk_text": "场景2"},
            },
            {
                "metadata": {
                    "context_state": {
                        "scene_id": "scene_3",
                        "scene_version": 1,
                        "boundary": {
                            "type": "chapter_transition",
                            "chapter_id": "ch2",
                            "scene_id": "scene_3",
                            "confidence": 0.95,
                        },
                    }
                },
                "source": {"chunk_text": "第2章 场景3"},
            },
        ]

        result = build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)

        assert len(result.chapters) == 2
        assert result.chapters[0].chapter_id == "ch1"
        assert result.chapters[0].scene_ids == ("scene_1", "scene_2")
        assert result.chapters[1].chapter_id == "ch2"
        assert result.chapters[1].scene_ids == ("scene_3",)

        reconstructed = "".join(
            txt_body[c.start_position:c.end_position]
            for c in result.chapters
        )
        assert reconstructed == txt_body

    def test_production_chapter_id_in_boundary_object(self):
        """Regression test: chapter_id must be read from boundary.chapter_id (production structure).

        RM-8.2 runtime places chapter_id inside boundary object:
        {
            "metadata": {
                "context_state": {
                    "scene_id": "scene_1",
                    "boundary": {
                        "type": "chapter_transition",
                        "chapter_id": "real_ch1",  # <-- actual location
                        "scene_id": "scene_1",
                        "confidence": 0.95
                    }
                }
            }
        }

        This test ensures Priority 1 provenance works with actual production structure.
        """
        translated_chunks = [
            "第1章 开始",
            "第二场景继续",
            "第2章 转折",
        ]
        txt_body = _assemble(translated_chunks)

        # Production-shaped records: chapter_id ONLY in boundary object
        chunk_records = [
            {
                "metadata": {
                    "context_state": {
                        "scene_id": "scene_1",
                        "scene_version": 1,
                        "boundary": {
                            "type": "chapter_transition",
                            "chapter_id": "real_ch1",
                            "scene_id": "scene_1",
                            "confidence": 0.95,
                        },
                    }
                },
                "source": {"chunk_text": "第1章 开始"},
            },
            {
                "metadata": {
                    "context_state": {
                        "scene_id": "scene_2",
                        "scene_version": 1,
                        "boundary": {
                            "type": "scene_transition",
                            "chapter_id": "real_ch1",
                            "scene_id": "scene_2",
                            "confidence": 0.9,
                        },
                    }
                },
                "source": {"chunk_text": "第二场景继续"},
            },
            {
                "metadata": {
                    "context_state": {
                        "scene_id": "scene_3",
                        "scene_version": 1,
                        "boundary": {
                            "type": "chapter_transition",
                            "chapter_id": "real_ch2",
                            "scene_id": "scene_3",
                            "confidence": 0.95,
                        },
                    }
                },
                "source": {"chunk_text": "第2章 转折"},
            },
        ]

        result = build_reader_chapter_map(txt_body=txt_body, translated_chunks=translated_chunks, chunk_records=chunk_records)

        # Priority 1 provenance must be used
        assert len(result.chapters) == 2
        assert result.chapters[0].chapter_id == "real_ch1"
        assert result.chapters[1].chapter_id == "real_ch2"
        assert result.chapters[0].scene_ids == ("scene_1", "scene_2")
        assert result.chapters[1].scene_ids == ("scene_3",)

        # Content preservation
        reconstructed = "".join(
            txt_body[c.start_position:c.end_position]
            for c in result.chapters
        )
        assert reconstructed == txt_body