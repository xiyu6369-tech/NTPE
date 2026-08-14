"""Contract tests for Rm8DeliveryAdapter."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.adapters.rm8_delivery_adapter import (
    DeliveryAdapterResult,
    DeliveryRequest,
    Rm8DeliveryAdapter,
)


class TestRm8DeliveryAdapter:
    def setup_method(self):
        self.adapter = Rm8DeliveryAdapter()

    def create_mock_delivery_result(self, status="success", error=None, manifest_path=None, qc_certificate_path=None, epub_path=None, pdf_path=None):
        """Create a mock DeliveryResult."""
        from types import SimpleNamespace
        return SimpleNamespace(
            status=status,
            error=error,
            manifest_path=manifest_path,
            qc_certificate_path=qc_certificate_path,
            epub_path=epub_path,
            pdf_path=pdf_path,
            output_path="/path/to/output",
        )

    def test_trigger_delivery_success(self, tmp_path: Path):
        """Test successful delivery trigger."""
        request = DeliveryRequest(
            assembled_text="Translated text",
            translated_chunks=["chunk1", "chunk2"],
            chunk_records=[{"index": 0}, {"index": 1}],
            locked_dictionary={"term": "translation"},
            options=MagicMock(quality_delivery_v83=True, quality_delivery_formats_v83=("txt", "epub")),
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
        )

        manifest_path = tmp_path / "manifest.json"
        manifest_data = {
            "novel_id": "test_novel",
            "generated_at": "2024-01-01T00:00:00",
            "pipeline_version": "1.0",
            "input_path": "/path/to/input.txt",
            "output_path": "/path/to/output",
            "chunk_total": 2,
            "chunk_size": 1000,
            "model": "test-model",
            "speed": "balanced",
            "quality_profile": "literary",
            "literary_quality": {},
            "context_continuity": {},
            "qc_result": {},
            "artifacts": {},
            "table_of_contents": [],
        }
        manifest_path.write_text(json.dumps(manifest_data))
        
        qc_path = tmp_path / "qc.json"
        qc_data = {
            "novel_id": "test_novel",
            "issued_at": "2024-01-01T00:00:00",
            "pipeline_version": "1.0",
            "overall_status": "pass",
            "overall_score": 0.95,
            "literary_quality_score": 0.9,
            "format_consistency_score": 0.95,
            "term_lock_compliance_score": 1.0,
            "completeness_score": 0.9,
            "context_continuity_score": 0.88,
            "checks": {},
            "literary_quality_aggregate": {},
            "context_continuity_aggregate": {},
        }
        qc_path.write_text(json.dumps(qc_data))
        
        epub_path = tmp_path / "output.epub"
        epub_path.write_bytes(b"EPUB content")
        
        pdf_path = tmp_path / "output.pdf"
        pdf_path.write_bytes(b"PDF content")

        mock_delivery_result = self.create_mock_delivery_result(
            status="success",
            manifest_path=str(manifest_path),
            qc_certificate_path=str(qc_path),
            epub_path=str(epub_path),
            pdf_path=str(pdf_path),
        )

        with patch("core.adapters.rm8_delivery_adapter.run_delivery_pipeline", return_value=mock_delivery_result):
            result = self.adapter.trigger_delivery(request)

        assert isinstance(result, DeliveryAdapterResult)
        assert result.status == "success"
        assert result.error is None
        assert result.manifest is not None
        assert result.quality_certificate is not None
        assert result.epub_path == epub_path
        assert result.pdf_path == pdf_path
        assert result.delivery_result == mock_delivery_result

    def test_trigger_delivery_failed(self, tmp_path: Path):
        """Test delivery trigger when pipeline fails."""
        request = DeliveryRequest(
            assembled_text="Translated text",
            translated_chunks=["chunk1"],
            chunk_records=[{"index": 0}],
            locked_dictionary={},
            options=MagicMock(quality_delivery_v83=True, quality_delivery_formats_v83=("txt",)),
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
        )

        mock_delivery_result = self.create_mock_delivery_result(
            status="failed",
            error="Delivery pipeline error",
        )

        with patch("core.adapters.rm8_delivery_adapter.run_delivery_pipeline", return_value=mock_delivery_result):
            result = self.adapter.trigger_delivery(request)

        assert result.status == "failed"
        assert result.error == "Delivery pipeline error"
        assert result.manifest is None
        assert result.quality_certificate is None
        assert result.epub_path is None
        assert result.pdf_path is None

    def test_trigger_delivery_exception(self, tmp_path: Path):
        """Test delivery trigger handles exceptions."""
        request = DeliveryRequest(
            assembled_text="Translated text",
            translated_chunks=["chunk1"],
            chunk_records=[{"index": 0}],
            locked_dictionary={},
            options=MagicMock(quality_delivery_v83=True, quality_delivery_formats_v83=("txt",)),
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
        )

        with patch("core.adapters.rm8_delivery_adapter.run_delivery_pipeline", side_effect=RuntimeError("Unexpected error")):
            result = self.adapter.trigger_delivery(request)

        assert result.status == "failed"
        assert result.error == "Unexpected error"
        assert result.manifest is None
        assert result.quality_certificate is None

    def test_is_delivery_enabled_true(self):
        """Test is_delivery_enabled returns True when v83 flag is set."""
        options = MagicMock(quality_delivery_v83=True)
        assert self.adapter.is_delivery_enabled(options) is True

    def test_is_delivery_enabled_false(self):
        """Test is_delivery_enabled returns False when v83 flag is not set."""
        options = MagicMock(quality_delivery_v83=False)
        assert self.adapter.is_delivery_enabled(options) is False

    def test_is_delivery_enabled_missing_attribute(self):
        """Test is_delivery_enabled returns False when attribute is missing."""
        options = MagicMock()
        del options.quality_delivery_v83
        assert self.adapter.is_delivery_enabled(options) is False

    def test_get_delivery_formats_default(self):
        """Test get_delivery_formats returns default when not specified."""
        options = MagicMock(quality_delivery_formats_v83=("txt", "epub"))
        formats = self.adapter.get_delivery_formats(options)
        assert formats == ("txt", "epub")

    def test_get_delivery_formats_default_tuple(self):
        """Test get_delivery_formats returns default tuple when attribute missing."""
        options = MagicMock()
        del options.quality_delivery_formats_v83
        formats = self.adapter.get_delivery_formats(options)
        assert formats == ("txt",)

    def test_delivery_result_mapping_manifest(self, tmp_path: Path):
        """Test delivery result correctly maps manifest."""
        request = DeliveryRequest(
            assembled_text="Text",
            translated_chunks=["chunk1"],
            chunk_records=[{"index": 0}],
            locked_dictionary={},
            options=MagicMock(quality_delivery_v83=True, quality_delivery_formats_v83=("txt",)),
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
        )

        manifest_path = tmp_path / "manifest.json"
        manifest_data = {
            "novel_id": "test_novel",
            "generated_at": "2024-01-01T00:00:00",
            "pipeline_version": "1.0",
            "input_path": "/path/to/input.txt",
            "output_path": "/path/to/output",
            "chunk_total": 1,
            "chunk_size": 1000,
            "model": "test-model",
            "speed": "balanced",
            "quality_profile": "literary",
            "literary_quality": {},
            "context_continuity": {},
            "qc_result": {},
            "artifacts": {},
            "table_of_contents": [],
        }
        manifest_path.write_text(json.dumps(manifest_data))

        mock_delivery_result = self.create_mock_delivery_result(
            status="success",
            manifest_path=str(manifest_path),
        )

        with patch("core.adapters.rm8_delivery_adapter.run_delivery_pipeline", return_value=mock_delivery_result):
            result = self.adapter.trigger_delivery(request)

        assert result.manifest is not None
        assert result.manifest.novel_id == "test_novel"
        assert result.manifest.chunk_total == 1

    def test_delivery_result_mapping_qc_certificate(self, tmp_path: Path):
        """Test delivery result correctly maps QC certificate."""
        request = DeliveryRequest(
            assembled_text="Text",
            translated_chunks=["chunk1"],
            chunk_records=[{"index": 0}],
            locked_dictionary={},
            options=MagicMock(quality_delivery_v83=True, quality_delivery_formats_v83=("txt",)),
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
        )

        qc_path = tmp_path / "qc.json"
        qc_data = {
            "novel_id": "test_novel",
            "issued_at": "2024-01-01T00:00:00",
            "pipeline_version": "1.0",
            "overall_status": "pass",
            "overall_score": 0.9,
            "literary_quality_score": 0.85,
            "format_consistency_score": 0.95,
            "term_lock_compliance_score": 1.0,
            "completeness_score": 0.9,
            "context_continuity_score": 0.88,
            "checks": {},
            "literary_quality_aggregate": {},
            "context_continuity_aggregate": {},
        }
        qc_path.write_text(json.dumps(qc_data))

        mock_delivery_result = self.create_mock_delivery_result(
            status="success",
            qc_certificate_path=str(qc_path),
        )

        with patch("core.adapters.rm8_delivery_adapter.run_delivery_pipeline", return_value=mock_delivery_result):
            result = self.adapter.trigger_delivery(request)

        assert result.quality_certificate is not None
        assert result.quality_certificate.overall_score == 0.9
        assert result.quality_certificate.overall_status == "pass"

    def test_delivery_flag_propagation(self, tmp_path: Path):
        """Test delivery flags are correctly propagated from options."""
        options_with_v83 = MagicMock(quality_delivery_v83=True, quality_delivery_formats_v83=("txt", "epub", "pdf"))
        options_without_v83 = MagicMock(quality_delivery_v83=False, quality_delivery_formats_v83=("txt",))

        assert self.adapter.is_delivery_enabled(options_with_v83) is True
        assert self.adapter.is_delivery_enabled(options_without_v83) is False
        assert self.adapter.get_delivery_formats(options_with_v83) == ("txt", "epub", "pdf")
        assert self.adapter.get_delivery_formats(options_without_v83) == ("txt",)

    def test_delivery_result_structure(self, tmp_path: Path):
        """Test DeliveryAdapterResult has all required fields."""
        request = DeliveryRequest(
            assembled_text="Text",
            translated_chunks=["chunk1"],
            chunk_records=[{"index": 0}],
            locked_dictionary={},
            options=MagicMock(quality_delivery_v83=True, quality_delivery_formats_v83=("txt",)),
            input_path=tmp_path / "input.txt",
            output_dir=tmp_path / "output",
        )

        mock_delivery_result = self.create_mock_delivery_result(status="success")

        with patch("core.adapters.rm8_delivery_adapter.run_delivery_pipeline", return_value=mock_delivery_result):
            result = self.adapter.trigger_delivery(request)

        assert hasattr(result, "delivery_result")
        assert hasattr(result, "manifest")
        assert hasattr(result, "quality_certificate")
        assert hasattr(result, "epub_path")
        assert hasattr(result, "pdf_path")
        assert hasattr(result, "status")
        assert hasattr(result, "error")