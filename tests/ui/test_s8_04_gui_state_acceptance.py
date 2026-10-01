"""S8-04 GUI Dry-Run & Result-State End-to-End Acceptance.

Verifies that the two GUI entry points present runtime result states truthfully:

* PySide6 Translation Studio (Tests A–F): dry-run, success, incomplete,
  failure, duplicate-launch — all via fake/mock workers.
* Tkinter Translation Launcher (Tests G–J): dry-run/result mapping at the
  worker/controller layer. ``TranslationLauncherApp`` cannot be constructed due
  to a pre-existing Tk pack/grid defect, so GUI-widget-level behavior is a
  documented coverage gap (Test J).

Provider = 0 · Network = 0 · Real translation = 0.
"""

from __future__ import annotations

import sys
from dataclasses import replace
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
from ui.translation_studio.resources.translations import Strings
from lts.txt_translation_runtime import TxtTranslationOptions
from core.epub_translation.runtime.adapter import EpubTranslationOptions
from core.epub_translation.contract import EpubMetadata, EpubTranslationInput
from core.launcher_product.config import load_launcher_config
from ui.translation_launcher.controller import LauncherController


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication(sys.argv)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

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


def _make_epub_options(source: Path, identifier: str = "id-1", dry_run: bool = False) -> EpubTranslationOptions:
    metadata = EpubMetadata(
        title="Test", author=None, language="ko", identifier=identifier,
        publisher=None, date=None, raw=MappingProxyType({}),
    )
    tin = EpubTranslationInput(
        source_epub_path=source, original_hash="a" * 64, extraction_status="success",
        warnings=(), metadata=metadata, chapter_map=(), resources=(),
        toc_entries=(), fixed_layout_info=None,
    )
    return EpubTranslationOptions(translation_input=tin, chunks=(), dry_run=dry_run)


class _NoTxtRuntime:
    def __init__(self, root=None):
        pass

    def translate_txt(self, options):
        raise AssertionError("EPUB execution must not use the TXT runtime")


# ---------------------------------------------------------------------------
# Test A — Studio TXT dry-run
# ---------------------------------------------------------------------------

def test_a_studio_txt_dry_run_state(qapp):
    class _DryRunTxtRuntime:
        def __init__(self, root=None):
            pass

        def translate_txt(self, options):
            return {
                "status": "dry_run", "input": str(options.input_path), "output": "",
                "output_dir": str(options.output_dir), "chunk_total": 2,
                "chunk_successful": 0, "chunk_failed": 0, "session_id": "dry",
            }

    options = TxtTranslationOptions(
        input_path=Path("input/test.txt"), output_dir=Path("output/test"), model="m", dry_run=True,
    )
    worker = TranslationWorker(options, Path("."))
    progress_events: list = []
    finished: dict = {}
    worker.progress_updated.connect(lambda p: progress_events.append(p))
    worker.translation_finished.connect(lambda r: finished.update(r))

    with patch("core.translation_runtime.TranslationRuntime", _DryRunTxtRuntime):
        worker.run()

    assert finished["status"] == "dry_run"
    assert progress_events[-1]["status"] == "dry_run"

    # UI mapping: dry_run must be shown as dry-run, never success/failure.
    page = ProjectPage()
    try:
        _add_txt_project(page)
        page.table.selectRow(0)
        page._current_translation_row = 0
        page._translation_runner = MagicMock()
        with patch("ui.translation_studio.pages.project_page.QMessageBox") as mb:
            page._on_translation_finished(finished)
        assert page._projects[0]["status"] == Strings.TRANSLATION_STATUS_DRY_RUN
        assert mb.information.called
        assert not mb.critical.called
        assert not mb.warning.called
        assert page._current_translation_row is None
        assert page._translation_runner is None
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Test B — Studio EPUB dry-run stays on canonical route
# ---------------------------------------------------------------------------

def test_b_studio_epub_dry_run_canonical(qapp, tmp_path):
    src_dir = tmp_path / "books"
    src_dir.mkdir()
    epub_path = src_dir / "book.epub"
    epub_path.write_text("x", encoding="utf-8")
    options = _make_epub_options(epub_path, identifier="id-1", dry_run=True)

    fake_tr = SimpleNamespace(
        aggregate_status="incomplete", total_chunks=2, success_count=0, failed_count=0,
        total_chapters=1, session_id="dry", chapter_results=(),
    )
    packed: list = []

    worker = TranslationWorker(options, tmp_path)
    finished: dict = {}
    worker.translation_finished.connect(lambda r: finished.update(r))

    with patch("core.epub_translation.runtime.adapter.translate_epub_translation_input", return_value=fake_tr) as m_tr, \
            patch("core.epub_translation.runtime.epub_packager.pack_epub_resource_aware", side_effect=lambda **k: packed.append(k)), \
            patch("core.epub_translation.reader_chapter_map.build_epub_reader_chapter_map_with_metadata", return_value=SimpleNamespace()), \
            patch("core.translation_runtime.TranslationRuntime", _NoTxtRuntime):
        worker.run()

    assert m_tr.called, "dry-run must still use the canonical EPUB runtime route"
    assert not packed, "dry-run must not produce a packaged EPUB"
    assert finished["status"] == "dry_run"
    assert finished["pipeline_mode"] == "epub"
    assert finished["output"] == ""


# ---------------------------------------------------------------------------
# Test C/D/E — Studio success / incomplete / failure result states
# ---------------------------------------------------------------------------

def _studio_epub_page_with_result(result: dict):
    page = ProjectPage()
    _add_epub_project(page, source="input/test.epub")
    page.table.selectRow(0)
    page._current_translation_row = 0
    page._translation_runner = MagicMock()
    return page


def test_c_studio_success_state(qapp):
    page = _studio_epub_page_with_result({})
    result = {
        "status": "success", "output": "books/output/epub_translation/id-1/book_zh.epub",
        "output_dir": "books/output/epub_translation/id-1", "chunk_total": 3,
        "chunk_successful": 3, "chunk_failed": 0, "session_id": "s",
    }
    try:
        with patch("ui.translation_studio.pages.project_page.QMessageBox.information") as info:
            page._on_translation_finished(result)
        assert page._projects[0]["status"] == Strings.TRANSLATION_STATUS_COMPLETED
        assert "成功區塊：3 / 3" in page._projects[0]["progress"]
        assert info.call_count == 1
        assert "book_zh.epub" in info.call_args[0][2]
        assert page._current_translation_row is None and page._translation_runner is None
    finally:
        page.close()


def test_d_studio_incomplete_state(qapp):
    page = _studio_epub_page_with_result({})
    result = {
        "status": "incomplete", "output": "books/output/epub_translation/id-1/book_zh.epub",
        "output_dir": "books/output/epub_translation/id-1", "chunk_total": 3,
        "chunk_successful": 2, "chunk_failed": 1, "error": "partial",
    }
    try:
        with patch("ui.translation_studio.pages.project_page.QMessageBox.warning") as warn, \
                patch("ui.translation_studio.pages.project_page.QMessageBox.information") as info:
            page._on_translation_finished(result)
        assert page._projects[0]["status"] == Strings.TRANSLATION_STATUS_INCOMPLETE
        assert "2/3 成功" in page._projects[0]["progress"]
        assert warn.called and not info.called
        assert page._current_translation_row is None and page._translation_runner is None
    finally:
        page.close()


def test_e_studio_failure_state(qapp):
    page = _studio_epub_page_with_result({})
    try:
        with patch("ui.translation_studio.pages.project_page.QMessageBox.critical") as crit, \
                patch("ui.translation_studio.pages.project_page.QMessageBox.information") as info:
            page._on_translation_finished({"status": "failed", "error": "boom"})
        assert page._projects[0]["status"] == Strings.TRANSLATION_STATUS_FAILED
        assert crit.called and not info.called
        # translating state released; row selectable again
        assert page._current_translation_row is None and page._translation_runner is None
        page.table.selectRow(0)
        assert page.btn_translate.isEnabled()
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Test F — Studio duplicate launch prevention
# ---------------------------------------------------------------------------

def test_f_studio_duplicate_launch_blocked(qapp):
    page = ProjectPage()
    try:
        _add_epub_project(page, source="input/test.epub")
        page.table.selectRow(0)
        options = _make_epub_options(Path("input/test.epub"), identifier="id-1")
        with patch.object(page, "_build_epub_options", return_value=options), \
                patch("ui.translation_studio.pages.project_page.TranslationRunner") as runner_cls, \
                patch("ui.translation_studio.pages.project_page.QMessageBox.information"):
            runner = MagicMock()
            runner_cls.return_value = runner
            page._on_translate()
            assert page._current_translation_row == 0 and runner.start.called
            runner.start.reset_mock()
            page._on_translate()
            assert not runner.start.called, "second launch must be blocked"
    finally:
        page.close()


# ---------------------------------------------------------------------------
# Tkinter launcher — worker/controller level (GUI construction is blocked)
# ---------------------------------------------------------------------------

class _FakeStatusText:
    def __init__(self):
        self.text = ""
        self.state = "normal"

    def configure(self, **kwargs):
        self.state = kwargs.get("state", self.state)

    def delete(self, *args):
        self.text = ""

    def insert(self, *args):
        if len(args) > 1:
            self.text += str(args[1])


class _FakeButton:
    def __init__(self):
        self.state = "normal"

    def config(self, **kwargs):
        self.state = kwargs.get("state", self.state)


def _make_tk_app():
    """Stand-in receiver for TranslationLauncherApp bound methods.

    The real app cannot be constructed (pre-existing Tk pack/grid defect), so the
    unbound result/state callbacks are exercised against this minimal object.
    """
    app = SimpleNamespace(
        status=_FakeStatusText(),
        start_button=_FakeButton(),
        dry_run_button=_FakeButton(),
        _translation_runner="running",
    )

    def _write_status(text, _status=app.status):
        _status.configure(state="normal")
        _status.delete("1.0", "end")
        _status.insert("1.0", text)
        _status.configure(state="disabled")

    app._write_status = _write_status
    return app


def _tk_call(method_name, app, *args):
    """Invoke an unbound TranslationLauncherApp method against a stand-in object."""
    from ui.translation_launcher.app import TranslationLauncherApp

    return getattr(TranslationLauncherApp, method_name)(app, *args)


# Test G — Tkinter dry-run state
def test_g_tkinter_worker_dry_run_progress():
    from ui.translation_launcher.worker import TranslationWorker as TkWorker

    options = TxtTranslationOptions(
        input_path=Path("input/test.txt"), output_dir=Path("output/test"), model="m", dry_run=True,
    )
    worker = TkWorker(options, Path("."))
    events: list = []
    worker.set_callbacks(lambda p: events.append(p), lambda r: None, lambda e: None)
    worker._emit_final_progress({"status": "dry_run", "chunk_total": 2, "chunk_successful": 0, "chunk_failed": 0})
    assert events[-1]["status"] == "dry_run"


def test_g_tkinter_dry_run_callback_state():
    from ui.translation_launcher import app as appmod

    app = _make_tk_app()
    with patch.object(appmod.messagebox, "showinfo") as info, \
            patch.object(appmod.messagebox, "showerror") as err, \
            patch.object(appmod.messagebox, "showwarning") as warn:
        _tk_call("_on_translation_finished", app, {"status": "dry_run", "output": "", "chunk_total": 2, "chunk_successful": 0})
    assert "Dry-Run" in app.status.text
    assert info.called and not err.called and not warn.called
    assert app.start_button.state == "normal" and app.dry_run_button.state == "normal"
    assert app._translation_runner is None


# Test H — Tkinter validation failure
def test_h_tkinter_validation_failure_blocks():
    controller = LauncherController(environment={"NVIDIA_API_KEY": "x"})
    invalid = replace(load_launcher_config(), input_path="", output_directory="")
    result = controller.validate(invalid)
    assert result.ready is False
    assert "input_file_missing" in {issue.code for issue in result.blocking_reasons}


# Test I — Tkinter success/failure/error mapping
def test_i_tkinter_success_mapping():
    from ui.translation_launcher import app as appmod

    app = _make_tk_app()
    with patch.object(appmod.messagebox, "showinfo") as info, \
            patch.object(appmod.messagebox, "showerror") as err, \
            patch.object(appmod.messagebox, "showwarning"):
        _tk_call("_on_translation_finished", app, {"status": "success", "output": "out/book_zh.txt", "chunk_total": 3, "chunk_successful": 3})
    assert "翻譯完成" in app.status.text and info.called and not err.called
    assert app._translation_runner is None


def test_i_tkinter_failure_and_error_mapping():
    from ui.translation_launcher import app as appmod

    app = _make_tk_app()
    with patch.object(appmod.messagebox, "showerror") as err, \
            patch.object(appmod.messagebox, "showinfo") as info, \
            patch.object(appmod.messagebox, "showwarning"):
        _tk_call("_on_translation_finished", app, {"status": "failed", "error": "boom"})
    assert "失敗" in app.status.text and err.called and not info.called
    assert app.start_button.state == "normal"

    app2 = _make_tk_app()
    with patch.object(appmod.messagebox, "showerror") as err, patch.object(appmod.messagebox, "showinfo"):
        _tk_call("_on_translation_error", app2, "network down")
    assert "錯誤" in app2.status.text and err.called
    assert app2._translation_runner is None


# Test J — Tkinter duplicate start (documented GUI-level coverage gap)
def test_j_tkinter_duplicate_start_documented_gap():
    """Duplicate-start prevention is implemented by disabling the Start/Dry-Run
    buttons during execution in ``TranslationLauncherApp``. Because the app cannot
    be constructed (pre-existing Tk pack/grid defect), the widget-level guard
    cannot be exercised here. This test records the seam and the gap; it is not a
    substitute for GUI-level verification.

    The controller intentionally has no API-level dedup; a single execution is
    enforced by the disabled button in the UI event loop.
    """
    controller = LauncherController()
    # The controller exposes start_translation but no dedup guard (by design).
    assert callable(controller.start_translation)
    assert not hasattr(controller, "is_running")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
