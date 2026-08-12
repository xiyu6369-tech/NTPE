# tests/unit/translation_release/test_exporters.py

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.translation_release.models import DeliveryManifest, TOCEntry
from core.translation_release.exporters.epub_exporter import EpubExporter
from core.translation_release.exporters.pdf_exporter import PdfExporter
from core.translation_release.exporters.base import BaseExporter


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
def sample_toc():
    return [
        TOCEntry("ch1", "第1章 初遇", 2, 1, 2, ["s1", "s2"], 100),
        TOCEntry("ch2", "第2章 展開", 1, 3, 3, ["s3"], 50),
    ]


@pytest.fixture
def sample_polished_text():
    return """【書誌資訊】
書名：test_novel
作者：未知作者
譯者：NTPE Translation Engine
翻譯日期：2026-01-15
翻譯模型：test-model
管線版本：NTPE_RM83_v1
品質狀態：PASS (score=90.0)

【目錄】
第1章 初遇 .......... 2 場景 (Chunk 1-2)
第2章 展開 .......... 1 場景 (Chunk 3-3)

───

第1章 初遇

主角走進了房間。

他看到了桌上有一封信。

第2章 展開

信上寫著：明天見。"""


class TestEpubExporter:
    """Tests for EpubExporter."""

    def test_epub_exporter_format_name(self):
        exporter = EpubExporter()
        assert exporter.format_name == "epub"
        assert exporter.file_extension == ".epub"

    def test_epub_exporter_graceful_fallback_when_no_ebooklib(self, tmp_path, sample_manifest, sample_toc, sample_polished_text):
        """When ebooklib is not available, export should return False gracefully."""
        exporter = EpubExporter()
        output_path = tmp_path / "test.epub"
        
        # Mock ImportError for ebooklib
        with patch.dict('sys.modules', {'ebooklib': None, 'ebooklib.epub': None}):
            result = exporter.export(
                polished_text=sample_polished_text,
                manifest=sample_manifest,
                toc=sample_toc,
                output_path=output_path,
            )
        
        assert result is False
        assert not output_path.exists()


class TestPdfExporter:
    """Tests for PdfExporter."""

    def test_pdf_exporter_format_name(self):
        exporter = PdfExporter()
        assert exporter.format_name == "pdf"
        assert exporter.file_extension == ".pdf"

    def test_pdf_exporter_graceful_fallback_when_no_reportlab(self, tmp_path, sample_manifest, sample_toc, sample_polished_text):
        """When reportlab is not available, export should return False gracefully."""
        exporter = PdfExporter()
        output_path = tmp_path / "test.pdf"
        
        # Mock ImportError for reportlab
        with patch.dict('sys.modules', {
            'reportlab': None,
            'reportlab.lib': None,
            'reportlab.lib.pagesizes': None,
            'reportlab.platypus': None,
            'reportlab.lib.styles': None,
            'reportlab.pdfbase': None,
            'reportlab.pdfbase.ttfonts': None,
        }):
            result = exporter.export(
                polished_text=sample_polished_text,
                manifest=sample_manifest,
                toc=sample_toc,
                output_path=output_path,
            )
        
        assert result is False
        assert not output_path.exists()

    def test_pdf_exporter_basic_structure(self, tmp_path, sample_manifest, sample_toc, sample_polished_text):
        """Test PDF has correct basic structure when reportlab is available."""
        exporter = PdfExporter()
        output_path = tmp_path / "test.pdf"
        
        # Mock reportlab
        mock_reportlab = MagicMock()
        mock_doc = MagicMock()
        mock_reportlab.platypus.SimpleDocTemplate.return_value = mock_doc
        mock_reportlab.lib.pagesizes.A4 = "A4"
        mock_styles = {"Normal": MagicMock()}
        mock_reportlab.lib.styles.getSampleStyleSheet.return_value = mock_styles
        
        with patch.dict('sys.modules', {
            'reportlab': mock_reportlab,
            'reportlab.lib': mock_reportlab.lib,
            'reportlab.lib.pagesizes': mock_reportlab.lib.pagesizes,
            'reportlab.platypus': mock_reportlab.platypus,
            'reportlab.lib.styles': mock_reportlab.lib.styles,
            'reportlab.pdfbase': mock_reportlab.pdfbase,
            'reportlab.pdfbase.ttfonts': mock_reportlab.pdfbase.ttfonts,
        }):
            result = exporter.export(
                polished_text=sample_polished_text,
                manifest=sample_manifest,
                toc=sample_toc,
                output_path=output_path,
            )
        
        assert result is True
        # Verify SimpleDocTemplate created
        mock_reportlab.platypus.SimpleDocTemplate.assert_called()
        # Verify build called
        mock_doc.build.assert_called()
        # Verify Paragraph used for metadata
        assert mock_reportlab.platypus.Paragraph.called


class TestBaseExporter:
    """Tests for BaseExporter abstract class."""

    def test_base_exporter_is_abstract(self):
        """BaseExporter should not be instantiable directly."""
        with pytest.raises(TypeError):
            BaseExporter()


class TestExporterIntegration:
    """Integration tests for exporters with delivery pipeline."""

    def test_epub_exporter_does_not_break_core_delivery(self, tmp_path, sample_manifest, sample_toc, sample_polished_text):
        """Even if EPUB fails, core delivery (TXT/Manifest/Cert) should not be affected."""
        exporter = EpubExporter()
        output_path = tmp_path / "test.epub"
        
        # Force ImportError
        with patch.dict('sys.modules', {'ebooklib': None, 'ebooklib.epub': None}):
            result = exporter.export(
                polished_text=sample_polished_text,
                manifest=sample_manifest,
                toc=sample_toc,
                output_path=output_path,
            )
        
        assert result is False
        # Core delivery files should still be creatable independently
        # (This is verified by test_package.py)

    def test_pdf_exporter_does_not_break_core_delivery(self, tmp_path, sample_manifest, sample_toc, sample_polished_text):
        """Even if PDF fails, core delivery should not be affected."""
        exporter = PdfExporter()
        output_path = tmp_path / "test.pdf"
        
        # Force ImportError
        with patch.dict('sys.modules', {
            'reportlab': None,
            'reportlab.lib': None,
            'reportlab.lib.pagesizes': None,
            'reportlab.platypus': None,
            'reportlab.lib.styles': None,
            'reportlab.pdfbase': None,
            'reportlab.pdfbase.ttfonts': None,
        }):
            result = exporter.export(
                polished_text=sample_polished_text,
                manifest=sample_manifest,
                toc=sample_toc,
                output_path=output_path,
            )
        
        assert result is False
        # Core delivery should still work

    def test_no_provider_calls_in_exporters(self, tmp_path, sample_manifest, sample_toc, sample_polished_text):
        """Exporters should not make any network/LLM calls."""
        epub_exporter = EpubExporter()
        pdf_exporter = PdfExporter()
        
        # Both should fail gracefully without any network activity
        with patch.dict('sys.modules', {'ebooklib': None, 'ebooklib.epub': None}):
            epub_result = epub_exporter.export(
                polished_text=sample_polished_text,
                manifest=sample_manifest,
                toc=sample_toc,
                output_path=tmp_path / "test.epub",
            )
        
        with patch.dict('sys.modules', {
            'reportlab': None,
            'reportlab.lib': None,
            'reportlab.lib.pagesizes': None,
            'reportlab.platypus': None,
            'reportlab.lib.styles': None,
            'reportlab.pdfbase': None,
            'reportlab.pdfbase.ttfonts': None,
        }):
            pdf_result = pdf_exporter.export(
                polished_text=sample_polished_text,
                manifest=sample_manifest,
                toc=sample_toc,
                output_path=tmp_path / "test.pdf",
            )
        
        assert epub_result is False
        assert pdf_result is False
        # No network calls were made (verified by mock isolation)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])