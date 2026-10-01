"""S8-03 TXT/EPUB Output Path & Result Policy — acceptance coverage.

Verifies the audited output contracts of the PySide6 Translation Studio:

* Test A — TXT: the UI-selected project output folder is the same directory the
  runtime writes the final ``*_zh.txt`` artifact into.
* Test B — EPUB: the final ``*_zh.epub`` artifact is produced by the canonical
  EPUB runtime/packager at a source-adjacent location; the UI does not select it.
* Test C — result-state path reporting: ``output`` and ``output_dir`` are
  semantically consistent for both pipelines.
* Test D — S8-01 preservation: EPUB launch routes to ``EpubTranslationOptions``
  and never falls back to the TXT runtime.

All tests use fake/mock runtimes: provider = 0, network = 0, real translation = 0.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.translation_studio.pages.project_page import ProjectPage
from ui.translation_studio.translation_worker import TranslationWorker
from lts.txt_translation_runtime import TxtTranslationOptions
from core.epub_translation.runtime.adapter import EpubTranslationOptions
from core.epub_translation.contract import EpubMetadata, EpubTranslationInput


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication(sys.argv)


def _add_txt_project(page: ProjectPage, source: str = "input/test.txt") -> None:
    page.add_project(
        name="Test Novel",
        source=source,
        status="已匯入",
        progress="0%",
        book_info={
            "title": "Test Novel",
            "source": source,
            "preview_text": "Chapter 1\n\nTest content.",
            "status": "ready",
            "warnings": [],
        },
    )


def _add_epub_project(page: ProjectPage, source: str = "input/test.epub") -> None:
    page.add_project(
        name="Test EPUB",
        source=source,
        status="已匯入",
        progress="0%",
        book_info={
            "title": "Test EPUB",
            "source": source,
            "preview_text": "Content",
            "status": "success",
            "warnings": [],
            "chapter_map": [
                {"index": 1, "title": "Chapter 1", "start_offset": 0, "end_offset": 100}
            ],
        },
    )


def _make_epub_options(source: Path, identifier: str = "id-1") -> EpubTranslationOptions:
    metadata = EpubMetadata(
        title="Test",
        author=None,
        language="ko",
        identifier=identifier,
        publisher=None,
        date=None,
        raw=MappingProxyType({}),
    )
    translation_input = EpubTranslationInput(
        source_epub_path=source,
        original_hash="a" * 64,
        extraction_status="success",
        warnings=(),
        metadata=metadata,
        chapter_map=(),
        resources=(),
        toc_entries=(),
        fixed_layout_info=None,
    )
    return EpubTranslationOptions(translation_input=translation_input, chunks=())


# ---------------------------------------------------------------------------
# Test A — TXT output path
# ---------------------------------------------------------------------------

def test_a1_txt_ui_selects_project_output_folder(qapp):
    """The UI derives and forwards the TXT project output folder."""
    page = ProjectPage()
    try:
        _add_txt_project(page, source="input/test.txt")
        page.table.selectRow(0)

        captured: dict = {}

        def _fake_runner(options, root_path):
            captured["options"] = options
            return MagicMock()

        with patch("ui.translation_studio.pages.project_page.TranslationRunner", side_effect=_fake_runner):
            page._on_translate()

        options = captured["options"]
        assert isinstance(options, TxtTranslationOptions)
        assert options.output_dir == Path("output") / "test"
    finally:
        page.close()


def test_a2_txt_worker_writes_artifact_in_selected_output_dir(tmp_path, qapp):
    """The TXT worker's final artifact lives inside options.output_dir."""
    class _FakeTxtRuntime:
        def __init__(self, root=None):
            self.root = root

        def translate_txt(self, options):
            final_output = options.output_dir / f"{options.input_path.stem}_zh.txt"
            final_output.parent.mkdir(parents=True, exist_ok=True)
            final_output.write_text("translated", encoding="utf-8")
            return {
                "status": "success",
                "input": str(options.input_path),
                "output": str(final_output),
                "output_dir": str(options.output_dir),
                "chunk_total": 1,
                "chunk_successful": 1,
                "chunk_failed": 0,
                "session_id": "fake-1",
            }

    input_path = tmp_path / "novel.txt"
    input_path.write_text("source", encoding="utf-8")
    output_dir = tmp_path / "out"
    options = TxtTranslationOptions(input_path=input_path, output_dir=output_dir, model="m", dry_run=True)

    worker = TranslationWorker(options, tmp_path)
    captured: dict = {}
    worker.translation_finished.connect(lambda r: captured.update(r))
    with patch("core.translation_runtime.TranslationRuntime", _FakeTxtRuntime):
        worker.run()

    assert captured["status"] == "success"
    artifact = Path(captured["output"])
    assert artifact == output_dir / "novel_zh.txt"
    assert artifact.exists()
    assert artifact.parent == Path(captured["output_dir"])


# ---------------------------------------------------------------------------
# Test B — EPUB output path
# ---------------------------------------------------------------------------

def test_b_epub_worker_output_is_canonical_source_adjacent(tmp_path, qapp):
    """EPUB final artifact is produced by the canonical runtime at a source-adjacent path."""
    src_dir = tmp_path / "books"
    src_dir.mkdir()
    epub_path = src_dir / "book.epub"
    epub_path.write_text("epub-bytes", encoding="utf-8")

    options = _make_epub_options(epub_path, identifier="id-9")

    fake_translation_result = SimpleNamespace(
        aggregate_status="success",
        total_chunks=2,
        success_count=2,
        failed_count=0,
        total_chapters=1,
        session_id="sess-9",
        chapter_results=(),
    )
    fake_reader_result = SimpleNamespace(reader_chapter_map=SimpleNamespace(chapters=()))

    def _fake_pack(packaging_input, output_path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("packaged-epub", encoding="utf-8")
        return SimpleNamespace(success=True, output_path=output_path, error_message="")

    class _NoTxtRuntime:
        def __init__(self, root=None):
            pass

        def translate_txt(self, options):
            raise AssertionError("EPUB execution must not use the TXT runtime")

    worker = TranslationWorker(options, tmp_path)
    captured: dict = {}
    worker.translation_finished.connect(lambda r: captured.update(r))

    with patch("core.epub_translation.runtime.adapter.translate_epub_translation_input", return_value=fake_translation_result), \
            patch("core.epub_translation.reader_chapter_map.build_epub_reader_chapter_map_with_metadata", return_value=fake_reader_result), \
            patch("core.epub_translation.runtime.epub_packager.pack_epub_resource_aware", side_effect=_fake_pack), \
            patch("core.translation_runtime.TranslationRuntime", _NoTxtRuntime):
        worker.run()

    expected_dir = src_dir / "output" / "epub_translation" / "id-9"
    expected_artifact = expected_dir / "book_zh.epub"
    assert captured["status"] == "success"
    assert captured["pipeline_mode"] == "epub"
    assert Path(captured["output"]) == expected_artifact
    assert Path(captured["output_dir"]) == expected_dir
    assert expected_artifact.exists()


def test_b_epub_ui_does_not_supply_output_path(qapp):
    """The EPUB UI call path carries no UI-selected output destination."""
    page = ProjectPage()
    try:
        _add_epub_project(page, source="input/test.epub")
        page.table.selectRow(0)

        options = _make_epub_options(Path("input/test.epub"), identifier="id-1")
        with patch.object(page, "_build_epub_options", return_value=options) as mock_build, \
                patch("ui.translation_studio.pages.project_page.TranslationRunner") as mock_runner_cls:
            mock_runner_cls.return_value = MagicMock()
            page._on_translate()

        assert mock_build.called
        # Clarified contract: only (project, source_path) are passed; no output dir.
        assert len(mock_build.call_args.args) == 2
        assert "output_dir" not in mock_build.call_args.kwargs
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Test C — result-state path reporting consistency
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "result",
    [
        {
            "status": "success",
            "output": "output/test/test_zh.txt",
            "output_dir": "output/test",
            "chunk_total": 3,
            "chunk_successful": 3,
            "chunk_failed": 0,
            "session_id": "s",
        },
        {
            "status": "success",
            "output": "books/output/epub_translation/id-1/test_zh.epub",
            "output_dir": "books/output/epub_translation/id-1",
            "chunk_total": 3,
            "chunk_successful": 3,
            "chunk_failed": 0,
            "session_id": "s",
        },
    ],
)
def test_c_success_result_path_consistent(qapp, result):
    page = ProjectPage()
    try:
        _add_epub_project(page, source="input/test.epub")
        page.table.selectRow(0)
        page._current_translation_row = 0
        page._translation_runner = MagicMock()

        # output must live inside the reported output_dir
        assert Path(result["output"]).parent == Path(result["output_dir"])

        with patch("ui.translation_studio.pages.project_page.QMessageBox.information") as mock_info:
            page._on_translation_finished(result)
            assert page._projects[0]["status"] == "翻譯完成"
            shown = mock_info.call_args[0][2]
            assert Path(result["output"]).name in shown
    finally:
        page.close()


def test_c_dry_run_is_not_success_or_incomplete(qapp):
    """dry_run results are mapped to an explicit dry-run state (see S8-04),
    never to success/incomplete/failure."""
    from ui.translation_studio.resources.translations import Strings

    page = ProjectPage()
    try:
        _add_txt_project(page, source="input/test.txt")
        page.table.selectRow(0)
        page._current_translation_row = 0
        page._translation_runner = MagicMock()

        with patch("ui.translation_studio.pages.project_page.QMessageBox"):
            page._on_translation_finished({"status": "dry_run", "output": "", "output_dir": "output/test"})

        status = page._projects[0]["status"]
        assert status == Strings.TRANSLATION_STATUS_DRY_RUN
        assert status not in (Strings.TRANSLATION_STATUS_COMPLETED, Strings.TRANSLATION_STATUS_INCOMPLETE, Strings.TRANSLATION_STATUS_FAILED)
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Test D — S8-01 preservation
# ---------------------------------------------------------------------------

def test_d_epub_launch_routes_to_epub_options_not_txt(qapp):
    page = ProjectPage()
    try:
        _add_epub_project(page, source="input/test.epub")
        page.table.selectRow(0)

        options = _make_epub_options(Path("input/test.epub"), identifier="id-1")
        with patch.object(page, "_build_epub_options", return_value=options) as mock_build, \
                patch("ui.translation_studio.pages.project_page.TranslationRunner") as mock_runner_cls, \
                patch("ui.translation_studio.pages.project_page.TxtTranslationOptions") as mock_txt:
            mock_runner_cls.return_value = MagicMock()
            page._on_translate()

        assert mock_build.called
        assert not mock_txt.called, "EPUB launch must not construct TxtTranslationOptions"
        passed = mock_runner_cls.call_args[0][0]
        assert isinstance(passed, EpubTranslationOptions)
    finally:
        page.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
