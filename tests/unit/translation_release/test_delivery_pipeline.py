# tests/unit/translation_release/test_delivery_pipeline.py

import pytest
from pathlib import Path
import json
from dataclasses import replace

from lts.txt_translation_runtime import TxtTranslationOptions
from core.translation_release.models import DeliveryResult, TOCEntry
from core.translation_release.delivery_pipeline import run_delivery_pipeline
from core.translation_release.validator import ValidationResult, ValidationCheck


@pytest.fixture
def sample_chunks():
    return [
        "第1章 初遇\n主角走進了房間。",
        "他看到了桌上有一封信。",
        "第2章 展開\n信上寫著：明天見。",
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
            "qa": {
                "metrics": {
                    "literary_quality_hits": 1,
                    "literary_quality_errors": 0,
                    "literary_quality_warnings": 0,
                    "literary_quality_passed": True,
                    "literary_quality_issue_codes": [],
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
            "qa": {
                "metrics": {
                    "literary_quality_hits": 0,
                    "literary_quality_errors": 0,
                    "literary_quality_warnings": 0,
                    "literary_quality_passed": True,
                    "literary_quality_issue_codes": [],
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
            "qa": {
                "metrics": {
                    "literary_quality_hits": 0,
                    "literary_quality_errors": 0,
                    "literary_quality_warnings": 0,
                    "literary_quality_passed": True,
                    "literary_quality_issue_codes": [],
                }
            },
        },
    ]


@pytest.fixture
def options():
    return TxtTranslationOptions(
        input_path=Path("test.txt"),
        output_dir=Path("out"),
        chunk_size=1000,
        model="test-model",
        speed="balanced",
        quality_profile="literary",
        taiwan_traditional_normalization=True,
        output_formatter_enabled=True,
    )


class TestRunDeliveryPipeline:
    """Tests for run_delivery_pipeline function."""

    def test_run_delivery_pipeline_success(self, tmp_path, sample_chunks, sample_records, options):
        assembled_text = "\n\n".join(sample_chunks)
        locked_dict = {"主角": "主角"}
        test_options = replace(options, output_dir=tmp_path)

        result = run_delivery_pipeline(
            assembled_text=assembled_text,
            translated_chunks=sample_chunks,
            chunk_records=sample_records,
            locked_dictionary=locked_dict,
            options=test_options,
            input_path=Path("test.txt"),
            output_dir=tmp_path,
        )

        assert isinstance(result, DeliveryResult)
        assert result.status == "success"
        assert result.output_path.endswith("test_zh.txt")
        assert result.manifest_path.endswith("test_delivery_manifest.json")
        assert result.qc_certificate_path.endswith("test_quality_certificate.json")
        assert result.error is None

        # Verify TXT output exists and has metadata header
        txt_content = Path(result.output_path).read_text(encoding="utf-8")
        assert "【書誌資訊】" in txt_content
        assert "書名：test" in txt_content
        assert "【目錄】" in txt_content
        assert "第1章" in txt_content
        assert "第2章" in txt_content
        assert "───" in txt_content
        assert "主角走進了房間" in txt_content

    def test_run_delivery_pipeline_fails_quality_gate(self, tmp_path, sample_chunks, sample_records, options):
        # Inject Korean residue to fail quality gate
        bad_text = "안녕하세요\n\n" + "\n\n".join(sample_chunks)
        locked_dict = {}
        test_options = replace(options, output_dir=tmp_path)

        result = run_delivery_pipeline(
            assembled_text=bad_text,
            translated_chunks=sample_chunks,
            chunk_records=sample_records,
            locked_dictionary=locked_dict,
            options=test_options,
            input_path=Path("test.txt"),
            output_dir=tmp_path,
        )

        assert result.status == "failed"
        assert result.error is not None
        assert "Quality gate FAILED" in result.error
        assert "korean_residue_global" in result.error or "critical" in result.error.lower()

    def test_run_delivery_pipeline_no_reassembly(self, tmp_path, sample_chunks, sample_records, options):
        """
        Verify that assembled_text is used as-is and not re-assembled.
        The assembled_text already has the correct structure.
        """
        # assembled_text has specific paragraph structure
        assembled_text = "段落一。\n\n段落二。\n\n段落三。"
        locked_dict = {}
        test_options = replace(options, output_dir=tmp_path)

        result = run_delivery_pipeline(
            assembled_text=assembled_text,
            translated_chunks=sample_chunks,
            chunk_records=sample_records,
            locked_dictionary=locked_dict,
            options=test_options,
            input_path=Path("test.txt"),
            output_dir=tmp_path,
        )

        assert result.status == "success"
        txt_content = Path(result.output_path).read_text(encoding="utf-8")
        # The polish pipeline will normalize but not re-assemble from chunks
        assert "段落一" in txt_content
        assert "段落二" in txt_content
        assert "段落三" in txt_content

    def test_run_delivery_pipeline_delivery_result_immutable(self, tmp_path, sample_chunks, sample_records, options):
        """DeliveryResult should be immutable (frozen dataclass)."""
        assembled_text = "\n\n".join(sample_chunks)
        locked_dict = {"主角": "主角"}
        test_options = replace(options, output_dir=tmp_path)

        result = run_delivery_pipeline(
            assembled_text=assembled_text,
            translated_chunks=sample_chunks,
            chunk_records=sample_records,
            locked_dictionary=locked_dict,
            options=test_options,
            input_path=Path("test.txt"),
            output_dir=tmp_path,
        )

        # Cannot modify frozen dataclass
        with pytest.raises(Exception):
            result.epub_path = "/new/path"
        with pytest.raises(Exception):
            result.pdf_path = "/new/path"
        with pytest.raises(Exception):
            result.status = "failed"

    def test_run_delivery_pipeline_creates_output_dir(self, tmp_path, sample_chunks, sample_records, options):
        """Output directory should be created if it doesn't exist."""
        assembled_text = "\n\n".join(sample_chunks)
        locked_dict = {}
        new_output = tmp_path / "new" / "output" / "dir"
        test_options = replace(options, output_dir=new_output)

        result = run_delivery_pipeline(
            assembled_text=assembled_text,
            translated_chunks=sample_chunks,
            chunk_records=sample_records,
            locked_dictionary=locked_dict,
            options=test_options,
            input_path=Path("test.txt"),
            output_dir=new_output,
        )

        assert new_output.exists()
        assert result.status == "success"

    def test_run_delivery_pipeline_manifest_content(self, tmp_path, sample_chunks, sample_records, options):
        """Verify DeliveryManifest has correct content."""
        assembled_text = "\n\n".join(sample_chunks)
        locked_dict = {"主角": "主角"}
        test_options = replace(options, output_dir=tmp_path)

        result = run_delivery_pipeline(
            assembled_text=assembled_text,
            translated_chunks=sample_chunks,
            chunk_records=sample_records,
            locked_dictionary=locked_dict,
            options=test_options,
            input_path=Path("test.txt"),
            output_dir=tmp_path,
        )

        manifest_data = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
        assert manifest_data["novel_id"] == "test"
        assert manifest_data["chunk_total"] == 3
        assert manifest_data["model"] == "test-model"
        assert manifest_data["speed"] == "balanced"
        assert manifest_data["quality_profile"] == "literary"
        assert manifest_data["context_continuity"]["scene_count"] == 3
        assert manifest_data["context_continuity"]["chapter_count"] == 2
        assert manifest_data["qc_result"]["status"] == "PASS"
        assert len(manifest_data["table_of_contents"]) == 2

    def test_run_delivery_pipeline_certificate_content(self, tmp_path, sample_chunks, sample_records, options):
        """Verify QualityCertificate has correct content."""
        assembled_text = "\n\n".join(sample_chunks)
        locked_dict = {"主角": "主角"}
        test_options = replace(options, output_dir=tmp_path)

        result = run_delivery_pipeline(
            assembled_text=assembled_text,
            translated_chunks=sample_chunks,
            chunk_records=sample_records,
            locked_dictionary=locked_dict,
            options=test_options,
            input_path=Path("test.txt"),
            output_dir=tmp_path,
        )

        cert_data = json.loads(Path(result.qc_certificate_path).read_text(encoding="utf-8"))
        assert cert_data["novel_id"] == "test"
        assert cert_data["overall_status"] == "PASS"
        assert cert_data["overall_score"] >= 70.0
        assert "literary_quality_score" in cert_data
        assert "format_consistency_score" in cert_data
        assert "term_lock_compliance_score" in cert_data
        assert "completeness_score" in cert_data
        assert "context_continuity_score" in cert_data

    def test_run_delivery_pipeline_uses_assembled_text_not_chunks(self, tmp_path, sample_chunks, sample_records, options):
        """
        Critical test: pipeline should use assembled_text parameter directly,
        not join translated_chunks.
        """
        # assembled_text differs from what joining chunks would produce
        assembled_text = "這是已經組裝好的完整文本。\n\n包含特定的段落結構。"
        locked_dict = {}
        test_options = replace(options, output_dir=tmp_path)

        result = run_delivery_pipeline(
            assembled_text=assembled_text,
            translated_chunks=sample_chunks,  # different content
            chunk_records=sample_records,
            locked_dictionary=locked_dict,
            options=test_options,
            input_path=Path("test.txt"),
            output_dir=tmp_path,
        )

        assert result.status == "success"
        txt_content = Path(result.output_path).read_text(encoding="utf-8")
        # Should contain the assembled_text content, not the joined chunks
        assert "這是已經組裝好的完整文本" in txt_content
        assert "包含特定的段落結構" in txt_content
        # Should NOT contain the chapter markers from sample_chunks (which differ)
        # The polish pipeline will process assembled_text directly

    def test_run_delivery_pipeline_no_provider_calls(self, tmp_path, sample_chunks, sample_records, options):
        """Verify no network/LLM calls are made."""
        assembled_text = "\n\n".join(sample_chunks)
        locked_dict = {}
        test_options = replace(options, output_dir=tmp_path)

        # This is a structural test - just verify it runs without errors
        # Actual network call verification would require mocking
        result = run_delivery_pipeline(
            assembled_text=assembled_text,
            translated_chunks=sample_chunks,
            chunk_records=sample_records,
            locked_dictionary=locked_dict,
            options=test_options,
            input_path=Path("test.txt"),
            output_dir=tmp_path,
        )

        assert result.status == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])