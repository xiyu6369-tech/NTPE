# tests/unit/translation_release/test_package.py

import pytest
from pathlib import Path
import json

from lts.txt_translation_runtime import TxtTranslationOptions
from core.translation_release.models import DeliveryManifest, QualityCertificate, DeliveryResult, TOCEntry
from core.translation_release.package import write_txt_delivery, write_json_delivery, write_delivery_package
from core.translation_release.validator import ValidationResult, ValidationCheck


@pytest.fixture
def sample_toc():
    return [
        TOCEntry("ch1", "第1章", 2, 1, 2, ["s1", "s2"], 100),
        TOCEntry("ch2", "第2章", 1, 3, 3, ["s3"], 50),
    ]


@pytest.fixture
def sample_manifest():
    return DeliveryManifest(
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


@pytest.fixture
def sample_certificate():
    return QualityCertificate(
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
        literary_quality_aggregate={"hits": 0},
        context_continuity_aggregate={"scene_count": 2},
    )


class TestWriteTxtDelivery:
    """Tests for write_txt_delivery function."""

    def test_write_txt_delivery_creates_file(self, tmp_path):
        text = "測試文本內容。\n\n第二段。"
        path = write_txt_delivery(text, tmp_path, "test_novel")
        assert Path(path).exists()
        assert Path(path).read_text(encoding="utf-8") == text
        assert "test_novel_zh.txt" in path

    def test_write_txt_delivery_creates_output_dir(self, tmp_path):
        output_dir = tmp_path / "subdir" / "output"
        text = "內容"
        path = write_txt_delivery(text, output_dir, "novel")
        assert Path(path).exists()
        assert output_dir.exists()


class TestWriteJsonDelivery:
    """Tests for write_json_delivery function."""

    def test_write_json_delivery_manifest(self, tmp_path, sample_manifest):
        path = write_json_delivery(sample_manifest, tmp_path, "test_novel", "delivery_manifest")
        assert Path(path).exists()
        assert "test_novel_delivery_manifest.json" in path

        data = json.loads(Path(path).read_text(encoding="utf-8"))
        assert data["novel_id"] == "test_novel"
        assert data["chunk_total"] == 3

    def test_write_json_delivery_certificate(self, tmp_path, sample_certificate):
        path = write_json_delivery(sample_certificate, tmp_path, "test_novel", "quality_certificate")
        assert Path(path).exists()
        assert "test_novel_quality_certificate.json" in path

        data = json.loads(Path(path).read_text(encoding="utf-8"))
        assert data["novel_id"] == "test_novel"
        assert data["overall_status"] == "PASS"

    def test_write_json_delivery_creates_output_dir(self, tmp_path):
        output_dir = tmp_path / "subdir" / "output"
        obj = QualityCertificate(
            novel_id="test",
            issued_at="2026-01-15T10:00:00",
            pipeline_version="v1",
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
        path = write_json_delivery(obj, output_dir, "novel", "suffix")
        assert Path(path).exists()
        assert output_dir.exists()


class TestWriteDeliveryPackage:
    """Tests for write_delivery_package function."""

    def test_write_delivery_package_creates_core_artifacts(self, tmp_path, sample_manifest, sample_certificate):
        text = "最終潤飾後的文本。\n\n包含多段。"
        result = write_delivery_package(
            polished_text=text,
            delivery_manifest=sample_manifest,
            quality_certificate=sample_certificate,
            output_dir=tmp_path,
            novel_id="test_novel",
            formats=("txt",),
        )

        assert isinstance(result, DeliveryResult)
        assert result.status == "success"
        assert result.output_path.endswith("test_novel_zh.txt")
        assert result.manifest_path.endswith("test_novel_delivery_manifest.json")
        assert result.qc_certificate_path.endswith("test_novel_quality_certificate.json")
        assert result.epub_path is None
        assert result.pdf_path is None

        # Verify files exist and content
        assert Path(result.output_path).read_text(encoding="utf-8") == text
        manifest_data = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
        assert manifest_data["novel_id"] == "test_novel"
        cert_data = json.loads(Path(result.qc_certificate_path).read_text(encoding="utf-8"))
        assert cert_data["overall_status"] == "PASS"

    def test_write_delivery_package_formats_tuple(self, tmp_path, sample_manifest, sample_certificate):
        text = "文本。"
        result = write_delivery_package(
            polished_text=text,
            delivery_manifest=sample_manifest,
            quality_certificate=sample_certificate,
            output_dir=tmp_path,
            novel_id="test_novel",
            formats=("txt", "epub", "pdf"),
        )
        # EPUB/PDF are not created by package.py (handled by delivery_pipeline)
        assert result.epub_path is None
        assert result.pdf_path is None

    def test_write_delivery_package_default_formats(self, tmp_path, sample_manifest, sample_certificate):
        text = "文本。"
        result = write_delivery_package(
            polished_text=text,
            delivery_manifest=sample_manifest,
            quality_certificate=sample_certificate,
            output_dir=tmp_path,
            novel_id="test_novel",
        )
        assert result.epub_path is None
        assert result.pdf_path is None


class TestDeliveryResultImmutable:
    """Tests verifying DeliveryResult is immutable."""

    def test_delivery_result_frozen(self, tmp_path, sample_manifest, sample_certificate):
        result = write_delivery_package(
            polished_text="text",
            delivery_manifest=sample_manifest,
            quality_certificate=sample_certificate,
            output_dir=tmp_path,
            novel_id="test",
        )
        with pytest.raises(Exception):
            result.epub_path = "/some/path"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])