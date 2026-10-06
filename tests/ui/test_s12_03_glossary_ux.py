"""S12-03 Glossary reader-facing workflow tests.

Hermetic: tmp ``NTPE_HOME``; mocked file dialog / message boxes; capturing fake
runner. No provider, no network, no real translation. Verifies the UI consumes the
S12-02 backend and persists through the canonical ReaderProject, not UI-local state.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.reader_project.manager import ReaderProjectManager
from ui.translation_studio.pages.project_page import ProjectPage

_DIALOG_OPEN = "ui.translation_studio.pages.project_page.QFileDialog.getOpenFileName"
_MSGBOX_WARNING = "ui.translation_studio.pages.project_page.QMessageBox.warning"
_MSGBOX_QUESTION = "ui.translation_studio.pages.project_page.QMessageBox.question"
_RUNNER = "ui.translation_studio.pages.project_page.TranslationRunner"


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication(sys.argv)


def _manager(tmp_path: Path) -> ReaderProjectManager:
    return ReaderProjectManager(home=tmp_path / "NTPE_HOME")


def _source(tmp_path: Path, name: str = "novel.txt") -> Path:
    path = tmp_path / name
    path.write_text("정태의는 일라이를 보았다.\n", encoding="utf-8")
    return path


def _glossary(tmp_path: Path, name: str = "glossary.txt", src: str = "정태의", dst: str = "鄭泰義") -> Path:
    path = tmp_path / name
    path.write_text(f"{src}={dst}\n일라이=伊萊\n", encoding="utf-8")
    return path


def _json_glossary(tmp_path: Path) -> Path:
    path = tmp_path / "glossary.json"
    path.write_text('{"정태의": "鄭泰義", "일라이": "伊萊"}', encoding="utf-8")
    return path


def _epub(tmp_path: Path) -> Path:
    path = tmp_path / "book.epub"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>""",
        )
        zf.writestr(
            "OEBPS/content.opf",
            """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="b">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Book</dc:title><dc:identifier id="b">u</dc:identifier><dc:language>ko</dc:language>
  </metadata>
  <manifest><item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/></manifest>
  <spine><itemref idref="ch1"/></spine>
</package>""",
        )
        body = "정태의는 일라이를 보았다. " * 60
        zf.writestr(
            "OEBPS/ch1.xhtml",
            f'<html xmlns="http://www.w3.org/1999/xhtml"><head><title>제1장</title></head>'
            f"<body><h1>제1장</h1><p>{body}</p></body></html>",
        )
    return path


def _page(manager: ReaderProjectManager) -> ProjectPage:
    page = ProjectPage()
    page.set_project_manager(manager)
    page.refresh_projects()
    return page


def _select_first(page: ProjectPage) -> int:
    page.table.selectRow(0)
    page._on_selection_changed()
    return 0


def _patch_dialog(path: Path):
    return patch(_DIALOG_OPEN, return_value=(str(path), ""))


# ---------------------------------------------------------------------------
# A — No glossary UI state
# ---------------------------------------------------------------------------

def test_a_no_glossary_state(qapp, tmp_path):
    manager = _manager(tmp_path)
    manager.create(_source(tmp_path), title="Novel")
    page = _page(manager)
    try:
        _select_first(page)
        assert page.lbl_glossary_status.text() == "未設定"
        assert page.btn_glossary_import.isEnabled()
        assert not page.btn_glossary_replace.isEnabled()
        assert not page.btn_glossary_detach.isEnabled()
    finally:
        page.close()


# ---------------------------------------------------------------------------
# B/C — Import valid TXT / JSON
# ---------------------------------------------------------------------------

def test_b_import_valid_txt(qapp, tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_source(tmp_path), title="Novel")
    page = _page(manager)
    try:
        _select_first(page)
        with _patch_dialog(_glossary(tmp_path)):
            page._on_glossary_import()
        reloaded = manager.load(project.project_id)
        assert reloaded.glossary is not None
        assert reloaded.glossary.term_count == 2
        assert "已啟用" in page.lbl_glossary_status.text()
        assert page.btn_glossary_replace.isEnabled()
        assert page.btn_glossary_detach.isEnabled()
    finally:
        page.close()


def test_c_import_valid_json(qapp, tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_source(tmp_path), title="Novel")
    page = _page(manager)
    try:
        _select_first(page)
        with _patch_dialog(_json_glossary(tmp_path)):
            page._on_glossary_import()
        assert manager.load(project.project_id).glossary.format == "json"
    finally:
        page.close()


# ---------------------------------------------------------------------------
# D — Invalid import leaves project unchanged
# ---------------------------------------------------------------------------

def test_d_invalid_import_leaves_project_unchanged(qapp, tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_source(tmp_path), title="Novel")
    bad = tmp_path / "bad.csv"
    bad.write_text("a,b\n", encoding="utf-8")
    page = _page(manager)
    try:
        _select_first(page)
        with _patch_dialog(bad), patch(_MSGBOX_WARNING) as warning:
            page._on_glossary_import()
        assert manager.load(project.project_id).glossary is None
        assert page.lbl_glossary_status.text() == "未設定"
        warning.assert_called_once()
    finally:
        page.close()


# ---------------------------------------------------------------------------
# E/F — Replace
# ---------------------------------------------------------------------------

def test_e_replace_active_glossary(qapp, tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_source(tmp_path), title="Novel")
    page = _page(manager)
    try:
        _select_first(page)
        with _patch_dialog(_glossary(tmp_path, "g1.txt", "정태의", "鄭泰義")):
            page._on_glossary_import()
        first_hash = manager.load(project.project_id).glossary.content_hash

        with _patch_dialog(_glossary(tmp_path, "g2.txt", "정태의", "鄭泰益")):
            page._on_glossary_import()
        reloaded = manager.load(project.project_id)
        assert reloaded.glossary.content_hash != first_hash
        assert manager.resolve_glossary(reloaded)["정태의"] == "鄭泰益"
    finally:
        page.close()


def test_f_replace_failure_preserves_old_glossary(qapp, tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_source(tmp_path), title="Novel")
    page = _page(manager)
    try:
        _select_first(page)
        with _patch_dialog(_glossary(tmp_path, "g1.txt", "정태의", "鄭泰義")):
            page._on_glossary_import()
        old_hash = manager.load(project.project_id).glossary.content_hash

        broken = tmp_path / "broken.json"
        broken.write_text("{not valid json", encoding="utf-8")
        with _patch_dialog(broken), patch(_MSGBOX_WARNING):
            page._on_glossary_import()

        reloaded = manager.load(project.project_id)
        assert reloaded.glossary is not None
        assert reloaded.glossary.content_hash == old_hash
        assert "已啟用" in page.lbl_glossary_status.text()
    finally:
        page.close()


# ---------------------------------------------------------------------------
# G — Detach
# ---------------------------------------------------------------------------

def test_g_detach_active_glossary(qapp, tmp_path):
    from PySide6.QtWidgets import QMessageBox

    manager = _manager(tmp_path)
    project = manager.create(_source(tmp_path), title="Novel")
    page = _page(manager)
    try:
        _select_first(page)
        with _patch_dialog(_glossary(tmp_path)):
            page._on_glossary_import()
        with patch(_MSGBOX_QUESTION, return_value=QMessageBox.StandardButton.Yes):
            page._on_glossary_detach()
        assert manager.load(project.project_id).glossary is None
        assert page.lbl_glossary_status.text() == "未設定"
    finally:
        page.close()


def test_g2_detach_cancelled_keeps_glossary(qapp, tmp_path):
    from PySide6.QtWidgets import QMessageBox

    manager = _manager(tmp_path)
    project = manager.create(_source(tmp_path), title="Novel")
    page = _page(manager)
    try:
        _select_first(page)
        with _patch_dialog(_glossary(tmp_path)):
            page._on_glossary_import()
        with patch(_MSGBOX_QUESTION, return_value=QMessageBox.StandardButton.No):
            page._on_glossary_detach()
        assert manager.load(project.project_id).glossary is not None
    finally:
        page.close()


# ---------------------------------------------------------------------------
# H — Restart / reload preserves glossary
# ---------------------------------------------------------------------------

def test_h_restart_preserves_glossary(qapp, tmp_path):
    home = tmp_path / "NTPE_HOME"
    manager = ReaderProjectManager(home=home)
    project = manager.create(_source(tmp_path), title="Novel")
    page = _page(manager)
    try:
        _select_first(page)
        with _patch_dialog(_glossary(tmp_path)):
            page._on_glossary_import()
    finally:
        page.close()

    # Fresh manager + page (restart) from the same home.
    manager2 = ReaderProjectManager(home=home)
    page2 = _page(manager2)
    try:
        _select_first(page2)
        assert manager2.load(project.project_id).glossary is not None
        assert "已啟用" in page2.lbl_glossary_status.text()
    finally:
        page2.close()


# ---------------------------------------------------------------------------
# I/J/K — Translation launch wiring
# ---------------------------------------------------------------------------

class _CapturingRunner:
    captured = None

    def __init__(self, options, root_path):
        _CapturingRunner.captured = options

    def start(self, **_kwargs):
        pass


def test_i_txt_launch_consumes_active_glossary(qapp, tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_source(tmp_path), title="Novel")
    page = _page(manager)
    try:
        _select_first(page)
        with _patch_dialog(_glossary(tmp_path)):
            page._on_glossary_import()
        _CapturingRunner.captured = None
        with patch(_RUNNER, _CapturingRunner):
            page._on_translate()
        options = _CapturingRunner.captured
        assert options is not None
        assert options.glossary_path is not None
        assert options.glossary_hash == manager.load(project.project_id).glossary.content_hash
    finally:
        page.close()


def test_j_epub_launch_consumes_active_glossary(qapp, tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_epub(tmp_path), format="epub", title="Book")
    page = _page(manager)
    try:
        _select_first(page)
        with _patch_dialog(_glossary(tmp_path)):
            page._on_glossary_import()
        _CapturingRunner.captured = None
        with patch(_RUNNER, _CapturingRunner):
            page._on_translate()
        options = _CapturingRunner.captured
        assert options is not None
        assert options.glossary_path is not None
        assert options.glossary_hash == manager.load(project.project_id).glossary.content_hash
    finally:
        page.close()


def test_k_no_glossary_launch_is_feature_off(qapp, tmp_path):
    manager = _manager(tmp_path)
    manager.create(_source(tmp_path), title="Novel")
    page = _page(manager)
    try:
        _select_first(page)
        _CapturingRunner.captured = None
        with patch(_RUNNER, _CapturingRunner):
            page._on_translate()
        options = _CapturingRunner.captured
        assert options is not None
        assert options.glossary_path is None
        assert options.glossary_hash is None
    finally:
        page.close()


def test_launch_blocked_when_active_glossary_corrupt(qapp, tmp_path):
    manager = _manager(tmp_path)
    project = manager.create(_source(tmp_path), title="Novel")
    page = _page(manager)
    try:
        _select_first(page)
        with _patch_dialog(_glossary(tmp_path)):
            page._on_glossary_import()
        Path(manager.load(project.project_id).glossary.stored_path).unlink()

        _CapturingRunner.captured = None
        with patch(_RUNNER, _CapturingRunner), patch(_MSGBOX_WARNING) as warning:
            page._on_translate()
        assert _CapturingRunner.captured is None  # launch blocked, no runner
        warning.assert_called_once()
    finally:
        page.close()
