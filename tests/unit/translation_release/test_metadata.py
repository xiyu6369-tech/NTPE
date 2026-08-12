# tests/unit/translation_release/test_metadata.py

import pytest
from pathlib import Path
from datetime import datetime

from lts.txt_translation_runtime import TxtTranslationOptions
from core.translation_release.models import TOCEntry, DeliveryManifest, QualityCertificate, DeliveryResult
from core.translation_release.metadata import (
    build_toc_from_chunk_records,
    inject_metadata_into_text,
    generate_delivery_manifest,
    generate_quality_certificate,
)
from core.translation_release.validator import ValidationResult, ValidationCheck


@pytest.fixture
def sample_chunks():
    return [
        "第1章 初遇\n\n主角走進了房間。",
        "他看到了桌上有一封信。",
        "第2章 展開\n\n信上寫著：明天見。",
    ]


@pytest.fixture
def sample_records():
    return [
        {
            "source": {"char_count": 50, "chunk_text": "주인공이 방에 들어갔다."},
            "metadata": {
                "context_state": {
                    "scene_id": "scene_1",
                    "chapter_id": "chapter_1",
                    "boundary": {"type": "same_scene"},
                }
            },
        },
        {
            "source": {"char_count": 45, "chunk_text": "그는 책상 위에 편지가 있는 것을 보았다."},
            "metadata": {
                "context_state": {
                    "scene_id": "scene_2",
                    "chapter_id": "chapter_1",
                    "boundary": {"type": "scene_transition"},
                }
            },
        },
        {
            "source": {"char_count": 48, "chunk_text": "편지에는 내일 보자고 쓰여 있었다."},
            "metadata": {
                "context_state": {
                    "scene_id": "scene_3",
                    "chapter_id": "chapter_2",
                    "boundary": {"type": "chapter_transition"},
                }
            },
        },
    ]


class TestTOCEntry:
    """Tests for TOCEntry dataclass."""

    def test_toc_entry_creation(self):
        entry = TOCEntry(
            chapter_id="chapter_1",
            chapter_title="第1章 初遇",
            scene_count=2,
            start_chunk_index=1,
            end_chunk_index=2,
            scene_ids=["scene_1", "scene_2"],
            word_count_estimate=100,
        )
        assert entry.chapter_id == "chapter_1"
        assert entry.chapter_title == "第1章 初遇"
        assert entry.scene_count == 2
        assert entry.start_chunk_index == 1
        assert entry.end_chunk_index == 2
        assert entry.scene_ids == ["scene_1", "scene_2"]
        assert entry.word_count_estimate == 100

    def test_toc_entry_frozen(self):
        entry = TOCEntry(
            chapter_id="chapter_1",
            chapter_title="第1章",
            scene_count=1,
            start_chunk_index=1,
            end_chunk_index=1,
            scene_ids=["scene_1"],
            word_count_estimate=50,
        )
        with pytest.raises(Exception):
            entry.chapter_title = "第2章"


class TestBuildTOCFromChunkRecords:
    """Tests for build_toc_from_chunk_records function."""

    def test_build_toc_basic(self, sample_chunks, sample_records):
        toc = build_toc_from_chunk_records(sample_records, sample_chunks)
        assert len(toc) == 2
        assert toc[0].chapter_id == "chapter_1"
        assert toc[1].chapter_id == "chapter_2"

    def test_toc_scene_count(self, sample_chunks, sample_records):
        toc = build_toc_from_chunk_records(sample_records, sample_chunks)
        assert toc[0].scene_count == 2  # scene_1, scene_2
        assert toc[1].scene_count == 1  # scene_3

    def test_toc_chunk_indices(self, sample_chunks, sample_records):
        toc = build_toc_from_chunk_records(sample_records, sample_chunks)
        assert toc[0].start_chunk_index == 1
        assert toc[0].end_chunk_index == 2
        assert toc[1].start_chunk_index == 3
        assert toc[1].end_chunk_index == 3

    def test_toc_chapter_title_from_explicit_marker(self, sample_chunks, sample_records):
        toc = build_toc_from_chunk_records(sample_records, sample_chunks)
        # First chapter has "第1章 初遇" in first chunk
        assert "第1章" in toc[0].chapter_title
        # Second chapter has "第2章 展開" in first chunk
        assert "第2章" in toc[1].chapter_title

    def test_toc_chapter_title_fallback_when_no_marker(self, sample_records):
        """When no explicit marker, fallback to deterministic 第N章."""
        chunks_no_marker = [
            "主角走進了房間。",
            "他看到了桌上有一封信。",
            "信上寫著：明天見。",
        ]
        toc = build_toc_from_chunk_records(sample_records, chunks_no_marker)
        # Chapter 1: no marker -> fallback
        assert toc[0].chapter_title == "第1章"
        # Chapter 2: no marker -> fallback
        assert toc[1].chapter_title == "第2章"

    def test_toc_word_count_estimate(self, sample_chunks, sample_records):
        toc = build_toc_from_chunk_records(sample_records, sample_chunks)
        # word_count_estimate is sum of non-whitespace chars in chapter chunks
        assert toc[0].word_count_estimate > 0
        assert toc[1].word_count_estimate > 0

    def test_toc_scene_ids_sorted(self, sample_chunks, sample_records):
        toc = build_toc_from_chunk_records(sample_records, sample_chunks)
        assert toc[0].scene_ids == ["scene_1", "scene_2"]
        assert toc[1].scene_ids == ["scene_3"]

    def test_toc_empty_inputs(self):
        toc = build_toc_from_chunk_records([], [])
        assert toc == []

    def test_toc_chapter_pattern_variations(self):
        """Test various chapter marker patterns."""
        records = [
            {"metadata": {"context_state": {"scene_id": "s1", "chapter_id": "ch1", "boundary": {"type": "same_scene"}}}},
            {"metadata": {"context_state": {"scene_id": "s2", "chapter_id": "ch2", "boundary": {"type": "chapter_transition"}}}},
            {"metadata": {"context_state": {"scene_id": "s3", "chapter_id": "ch3", "boundary": {"type": "chapter_transition"}}}},
        ]
        chunks = [
            "第 1 章 開始",  # spaced
            "Chapter 2 Title",  # English
            "CHAPTER 3",  # uppercase
        ]
        toc = build_toc_from_chunk_records(records, chunks)
        assert "第1章" in toc[0].chapter_title or "第 1 章" in toc[0].chapter_title
        assert "Chapter2" in toc[1].chapter_title  # spaces removed by .replace(" ", "")
        assert "CHAPTER3" in toc[2].chapter_title or "第3章" in toc[2].chapter_title


class TestInjectMetadataIntoText:
    """Tests for inject_metadata_into_text function."""

    def test_inject_metadata_basic(self):
        toc = [
            TOCEntry("ch1", "第1章", 2, 1, 2, ["s1", "s2"], 100),
            TOCEntry("ch2", "第2章", 1, 3, 3, ["s3"], 50),
        ]
        result = inject_metadata_into_text(
            "正文內容。",
            title="測試小說",
            author="測試作者",
            translator="NTPE Translation Engine",
            date="2026-01-15",
            model="test-model",
            pipeline_version="NTPE_RM83_v1",
            toc=toc,
            quality_cert_summary="PASS (85.5)",
        )
        assert "【書誌資訊】" in result
        assert "書名：測試小說" in result
        assert "作者：測試作者" in result
        assert "翻譯日期：2026-01-15" in result
        assert "翻譯模型：test-model" in result
        assert "管線版本：NTPE_RM83_v1" in result
        assert "品質狀態：PASS (85.5)" in result
        assert "【目錄】" in result
        assert "第1章" in result
        assert "第2章" in result
        assert "───" in result
        assert "正文內容。" in result

    def test_inject_metadata_default_author_translator(self):
        toc = []
        result = inject_metadata_into_text(
            "內容",
            title="書名",
            date="2026-01-15",
            model="model",
            pipeline_version="v1",
            toc=toc,
            quality_cert_summary="PASS",
        )
        assert "作者：未知作者" in result
        assert "譯者：NTPE Translation Engine" in result


class TestDeliveryManifest:
    """Tests for DeliveryManifest dataclass."""

    def test_delivery_manifest_creation(self):
        manifest = DeliveryManifest(
            novel_id="test_novel",
            generated_at="2026-01-15T10:00:00",
            pipeline_version="NTPE_RM83_v1",
            input_path="/input/test.txt",
            output_path="/output/test_zh.txt",
            chunk_total=3,
            chunk_size=1000,
            model="test-model",
            speed="balanced",
            quality_profile="literary",
            literary_quality={"hits": 0, "errors": 0, "warnings": 0, "passed": True, "issue_codes": []},
            context_continuity={"scene_count": 2, "chapter_count": 2, "scene_transitions": 1},
            qc_result={"status": "PASS", "score": 90.0, "checks": {}},
            artifacts={"txt": "/output/test_zh.txt"},
            table_of_contents=[{"chapter_id": "ch1", "title": "第1章", "scene_count": 2, "start_chunk": 1, "end_chunk": 2}],
        )
        assert manifest.novel_id == "test_novel"
        assert manifest.chunk_total == 3

    def test_delivery_manifest_to_dict(self):
        manifest = DeliveryManifest(
            novel_id="test_novel",
            generated_at="2026-01-15T10:00:00",
            pipeline_version="NTPE_RM83_v1",
            input_path="/input/test.txt",
            output_path="/output/test_zh.txt",
            chunk_total=3,
            chunk_size=1000,
            model="test-model",
            speed="balanced",
            quality_profile="literary",
            literary_quality={"hits": 0, "errors": 0, "warnings": 0, "passed": True, "issue_codes": []},
            context_continuity={"scene_count": 2, "chapter_count": 2, "scene_transitions": 1},
            qc_result={"status": "PASS", "score": 90.0, "checks": {}},
            artifacts={"txt": "/output/test_zh.txt"},
            table_of_contents=[{"chapter_id": "ch1", "title": "第1章", "scene_count": 2, "start_chunk": 1, "end_chunk": 2}],
        )
        d = manifest.to_dict()
        assert d["novel_id"] == "test_novel"
        assert d["chunk_total"] == 3
        assert isinstance(d["table_of_contents"], list)
        assert d["table_of_contents"][0]["title"] == "第1章"

    def test_delivery_manifest_frozen(self):
        manifest = DeliveryManifest(
            novel_id="test_novel",
            generated_at="2026-01-15T10:00:00",
            pipeline_version="NTPE_RM83_v1",
            input_path="/input/test.txt",
            output_path="/output/test_zh.txt",
            chunk_total=3,
            chunk_size=1000,
            model="test-model",
            speed="balanced",
            quality_profile="literary",
            literary_quality={},
            context_continuity={},
            qc_result={},
            artifacts={},
            table_of_contents=[],
        )
        with pytest.raises(Exception):
            manifest.novel_id = "other"


class TestQualityCertificate:
    """Tests for QualityCertificate dataclass."""

    def test_quality_certificate_creation(self):
        cert = QualityCertificate(
            novel_id="test_novel",
            issued_at="2026-01-15T10:00:00",
            pipeline_version="NTPE_RM83_v1",
            overall_status="PASS",
            overall_score=90.0,
            literary_quality_score=95.0,
            format_consistency_score=90.0,
            term_lock_compliance_score=100.0,
            completeness_score=85.0,
            context_continuity_score=95.0,
            checks={},
            literary_quality_aggregate={},
            context_continuity_aggregate={},
        )
        assert cert.overall_status == "PASS"
        assert cert.overall_score == 90.0

    def test_quality_certificate_to_dict(self):
        cert = QualityCertificate(
            novel_id="test_novel",
            issued_at="2026-01-15T10:00:00",
            pipeline_version="NTPE_RM83_v1",
            overall_status="PASS",
            overall_score=90.0,
            literary_quality_score=95.0,
            format_consistency_score=90.0,
            term_lock_compliance_score=100.0,
            completeness_score=85.0,
            context_continuity_score=95.0,
            checks={"paragraph_structure": {"passed": True, "score": 100.0, "severity": "critical", "details": {}}},
            literary_quality_aggregate={"hits": 0},
            context_continuity_aggregate={"scene_count": 2},
        )
        d = cert.to_dict()
        assert d["novel_id"] == "test_novel"
        assert d["overall_status"] == "PASS"
        assert d["checks"]["paragraph_structure"]["passed"] is True


class TestDeliveryResult:
    """Tests for DeliveryResult dataclass."""

    def test_delivery_result_creation(self):
        result = DeliveryResult(
            status="success",
            output_path="/output/test_zh.txt",
            manifest_path="/output/test_delivery_manifest.json",
            qc_certificate_path="/output/test_quality_certificate.json",
        )
        assert result.status == "success"
        assert result.epub_path is None
        assert result.pdf_path is None
        assert result.error is None

    def test_delivery_result_with_optional(self):
        result = DeliveryResult(
            status="success",
            output_path="/output/test_zh.txt",
            manifest_path="/output/test_delivery_manifest.json",
            qc_certificate_path="/output/test_quality_certificate.json",
            epub_path="/output/test.epub",
            pdf_path="/output/test.pdf",
            error=None,
        )
        assert result.epub_path == "/output/test.epub"
        assert result.pdf_path == "/output/test.pdf"

    def test_delivery_result_failed(self):
        result = DeliveryResult(
            status="failed",
            output_path="",
            manifest_path="",
            qc_certificate_path="",
            error="Validation failed",
        )
        assert result.status == "failed"
        assert result.error == "Validation failed"


class TestGenerateDeliveryManifest:
    """Tests for generate_delivery_manifest function."""

    def test_generate_delivery_manifest(self, sample_chunks, sample_records):
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
            chunk_size=1000,
            model="test-model",
            speed="balanced",
            quality_profile="literary",
        )
        qc_result = ValidationResult(
            overall_passed=True,
            overall_score=90.0,
            checks=[],
            failed_critical=[],
            failed_major=[],
        )
        toc = [
            TOCEntry("ch1", "第1章", 2, 1, 2, ["s1", "s2"], 100),
            TOCEntry("ch2", "第2章", 1, 3, 3, ["s3"], 50),
        ]
        manifest = generate_delivery_manifest(
            novel_id="test_novel",
            input_path="/input/test.txt",
            output_path="/output/test_zh.txt",
            chunk_records=sample_records,
            translated_chunks=sample_chunks,
            locked_dictionary={"主角": "主角"},
            options=options,
            literary_quality_aggregate={"hits": 0, "errors": 0, "warnings": 0, "passed": True, "issue_codes": []},
            qc_result=qc_result,
            toc=toc,
            artifact_paths={"txt": "/output/test_zh.txt", "manifest": "/output/test_delivery_manifest.json", "qc_certificate": "/output/test_quality_certificate.json"},
        )
        assert manifest.novel_id == "test_novel"
        assert manifest.chunk_total == 3
        assert manifest.model == "test-model"
        assert manifest.speed == "balanced"
        assert manifest.quality_profile == "literary"
        assert manifest.context_continuity["scene_count"] == 3
        assert manifest.context_continuity["chapter_count"] == 2
        assert manifest.context_continuity["scene_transitions"] == 1
        assert manifest.qc_result["status"] == "PASS"
        assert len(manifest.table_of_contents) == 2

    def test_generate_delivery_manifest_context_continuity(self, sample_chunks, sample_records):
        options = TxtTranslationOptions(
            input_path=Path("test.txt"),
            output_dir=Path("out"),
        )
        qc_result = ValidationResult(
            overall_passed=True,
            overall_score=90.0,
            checks=[],
            failed_critical=[],
            failed_major=[],
        )
        toc = [TOCEntry("ch1", "第1章", 3, 1, 3, ["s1", "s2", "s3"], 200)]
        manifest = generate_delivery_manifest(
            novel_id="test",
            input_path="in.txt",
            output_path="out.txt",
            chunk_records=sample_records,
            translated_chunks=sample_chunks,
            locked_dictionary={},
            options=options,
            literary_quality_aggregate={},
            qc_result=qc_result,
            toc=toc,
            artifact_paths={},
        )
        # scene_transitions should count from records
        assert manifest.context_continuity["scene_transitions"] >= 1


class TestGenerateQualityCertificate:
    """Tests for generate_quality_certificate function."""

    def test_generate_quality_certificate(self):
        qc_result = ValidationResult(
            overall_passed=True,
            overall_score=90.0,
            checks=[
                ValidationCheck("paragraph_structure", True, 100.0, {}, "critical"),
                ValidationCheck("punctuation_consistency", True, 95.0, {}, "major"),
                ValidationCheck("quote_balance", True, 90.0, {}, "minor"),
                ValidationCheck("locked_term_compliance", True, 100.0, {}, "major"),
                ValidationCheck("length_ratio_global", True, 85.0, {}, "major"),
                ValidationCheck("repeated_lines_global", True, 95.0, {}, "minor"),
                ValidationCheck("chinese_char_ratio", True, 95.0, {}, "minor"),
            ],
            failed_critical=[],
            failed_major=[],
        )
        cert = generate_quality_certificate(
            novel_id="test_novel",
            qc_result=qc_result,
            literary_quality_aggregate={"hits": 0, "errors": 0, "warnings": 0, "passed": True},
            context_continuity_aggregate={"scene_count": 2, "chapter_count": 1},
        )
        assert cert.overall_status == "PASS"
        assert cert.overall_score == 90.0
        assert cert.literary_quality_score == 95.0  # chinese_char_ratio
        assert cert.format_consistency_score == 90.0  # min of paragraph, punctuation, quote
        assert cert.term_lock_compliance_score == 100.0
        assert cert.completeness_score == 85.0
        assert cert.context_continuity_score == 95.0  # repeated_lines_global

    def test_generate_quality_certificate_fail(self):
        qc_result = ValidationResult(
            overall_passed=False,
            overall_score=50.0,
            checks=[
                ValidationCheck("paragraph_structure", False, 50.0, {}, "critical"),
            ],
            failed_critical=["paragraph_structure"],
            failed_major=[],
        )
        cert = generate_quality_certificate(
            novel_id="test",
            qc_result=qc_result,
            literary_quality_aggregate={},
            context_continuity_aggregate={},
        )
        assert cert.overall_status == "FAIL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])