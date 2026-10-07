"""S12-07 — Glossary EPUB real-adapter reader-first E2E re-verification.

Closes the S12-04 EPUB block that S12-06 unblocked. The full reader-first chain is
real except the external provider-execution boundary:

    ProjectPage -> import glossary -> ReaderProject persist -> fresh restart
    -> EPUB translate launch -> canonical EpubTranslationOptions
    -> real translate_epub_translation_input -> real validator
    -> real build_epub_reader_chapter_map -> real pack_epub_resource_aware
    -> persisted EPUB -> fresh zipfile read-back -> terminology effect

Only ``RuntimeOrchestrator.execute`` (external model execution) is a deterministic echo.
The EPUB adapter, extraction, intake, chunking, validation, reader map and packager are
all real, and the terminology change is produced only by the canonical
``_apply_locked_dictionary`` loaded from the Project-owned glossary snapshot (no
test-side ``replace``).

Placed under ``tests/integration`` (non-UI directory) because the shared Qt E2E session
has a pre-existing Windows access violation; ProjectPage is still driven for real,
synchronously on the main thread.
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.reader_project.manager import ReaderProjectManager
from ui.translation_studio.pages.project_page import ProjectPage

_DIALOG_OPEN = "ui.translation_studio.pages.project_page.QFileDialog.getOpenFileName"
_MSGBOX_WARNING = "ui.translation_studio.pages.project_page.QMessageBox.warning"
_MSGBOX_INFO = "ui.translation_studio.pages.project_page.QMessageBox.information"
_MSGBOX_CRITICAL = "ui.translation_studio.pages.project_page.QMessageBox.critical"
_MSGBOX_QUESTION = "ui.translation_studio.pages.project_page.QMessageBox.question"
_RUNNER = "ui.translation_studio.pages.project_page.TranslationRunner"
_ORCH_EXECUTE = "core.runtime_orchestrator.manager.RuntimeOrchestrator.execute"

_TERM_SRC = "TEST_TERM_A"
_TERM_A = "測試詞彙甲"
_TERM_B = "測試詞彙乙"
_KO_SRC = "정태의"
_KO_TGT = "鄭泰義"
_TITLES = ("Chapter One", "Chapter Two", "Chapter Three")


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication(sys.argv)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_epub(path: Path, linear=(True, False, True)) -> Path:
    """3 chapters (ch2 supplementary), 1 referenced image, glossary term in ch2."""
    manifest = ['<item id="img1" href="pic.png" media-type="image/png"/>']
    for i in range(1, 4):
        manifest.append(f'<item id="ch{i}" href="ch{i}.xhtml" media-type="application/xhtml+xml"/>')
    spine = "".join(
        f'<itemref idref="ch{i}"' + ("" if linear[i - 1] else ' linear="no"') + "/>"
        for i in range(1, 4)
    )
    opf = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="b">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
        '<dc:title>Glossary Offset Book</dc:title>'
        '<dc:identifier id="b">urn:uuid:s12-07-book</dc:identifier>'
        '<dc:language>ko</dc:language></metadata>'
        f"<manifest>{''.join(manifest)}</manifest><spine>{spine}</spine></package>"
    )
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0"?><container version="1.0" '
            'xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>'
            '<rootfile full-path="OEBPS/content.opf" '
            'media-type="application/oebps-package+xml"/></rootfiles></container>',
        )
        zf.writestr("OEBPS/content.opf", opf)
        zf.writestr("OEBPS/pic.png", b"\x89PNG\r\n\x1a\ns12-07")
        for i in range(1, 4):
            extra = f"{_TERM_SRC} 등장한다. {_KO_SRC}도 있다. " if i == 2 else ""
            body = extra + (f"제{i}장 본문입니다. " + "문장입니다. " * 220)
            img = '<p><img src="pic.png" alt="pic"/></p>' if i == 1 else ""
            zf.writestr(
                f"OEBPS/ch{i}.xhtml",
                '<html xmlns="http://www.w3.org/1999/xhtml">'
                f"<head><title>{_TITLES[i - 1]}</title></head>"
                f"<body><p>{body}</p>{img}</body></html>",
            )
    return path


def _glossary(tmp_path: Path, name: str, dst: str = _TERM_A, ko: bool = True) -> Path:
    path = tmp_path / name
    lines = [f"{_TERM_SRC} = {dst}"]
    if ko:
        lines.append(f"{_KO_SRC} = {_KO_TGT}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _manager(home: Path) -> ReaderProjectManager:
    return ReaderProjectManager(home=home)


def _page(manager: ReaderProjectManager) -> ProjectPage:
    page = ProjectPage()
    page.set_project_manager(manager)
    page.refresh_projects()
    return page


def _select_first(page: ProjectPage) -> None:
    page.table.selectRow(0)
    page._on_selection_changed()


def _patch_dialog(path: Path):
    return patch(_DIALOG_OPEN, return_value=(str(path), ""))


def _import_glossary_via_ui(page: ProjectPage, path: Path) -> None:
    with _patch_dialog(path):
        page._on_glossary_import()


def _fake_orchestrator_execute(self, chunk_text="", **kwargs):
    """Deterministic echo at the external provider-execution boundary only."""
    metadata = kwargs.get("metadata") or {}
    source = metadata.get("source", {}).get("chunk_text", chunk_text)
    return SimpleNamespace(
        response={"status": "success", "translation": source},
        metadata=None,
        session=None,
        request=None,
    )


class _RealEpubRunner:
    """Synchronous stand-in for the Qt runner that still runs the REAL adapter+packager.

    ``root_override`` keeps the canonical runtime hermetic (config / character memory
    under the test home) so the repository's ``memory/`` tree is never written.
    """

    captured: Any = None
    root_override: "Path | None" = None

    def __init__(self, options, root_path):
        _RealEpubRunner.captured = options
        self._options = options
        self._root = _RealEpubRunner.root_override or root_path

    def start(self, on_progress=None, on_finished=None, on_error=None):
        from ui.translation_studio.translation_worker import TranslationWorker

        result = TranslationWorker(self._options, self._root)._runtime_epub_translate(
            self._options
        )
        if on_finished is not None:
            on_finished(result)


def _launch_epub(page: ProjectPage, home: Path):
    _RealEpubRunner.captured = None
    _RealEpubRunner.root_override = home
    try:
        with patch(_RUNNER, _RealEpubRunner), patch(_ORCH_EXECUTE, _fake_orchestrator_execute), \
                patch(_MSGBOX_INFO), patch(_MSGBOX_WARNING), patch(_MSGBOX_CRITICAL):
            page._on_translate()
    finally:
        _RealEpubRunner.root_override = None
    return _RealEpubRunner.captured


def _read_epub(path: Path) -> dict:
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        opf_name = next(n for n in names if n.endswith(".opf"))
        data = {
            "names": names,
            "opf": zf.read(opf_name).decode("utf-8"),
            "xhtml": {},
        }
        for n in names:
            if n.endswith(".xhtml"):
                data["xhtml"][Path(n).name] = zf.read(n).decode("utf-8")
    return data


def _spine_idrefs(opf: str) -> list[str]:
    return re.findall(r'idref="([^"]+)"', opf)


# ===========================================================================
# 1. Main reader-first E2E: UI import -> restart -> real adapter -> persisted EPUB
# ===========================================================================

def test_s12_07_reader_first_real_adapter_e2e(qapp, tmp_path):
    home = tmp_path / "NTPE_HOME"
    manager = _manager(home)
    project = manager.create(_make_epub(tmp_path / "book.epub"), format="epub", title="Book")
    glossary_file = _glossary(tmp_path, "g.txt")

    page = _page(manager)
    try:
        _select_first(page)
        _import_glossary_via_ui(page, glossary_file)
        record = manager.load(project.project_id).glossary
        assert record is not None
        assert record.term_count == 2
        record_hash = record.content_hash
        assert "已啟用" in page.lbl_glossary_status.text()
    finally:
        page.close()

    # Fresh restart: new manager + page from the same home.
    manager2 = _manager(home)
    page2 = _page(manager2)
    try:
        _select_first(page2)
        reloaded = manager2.load(project.project_id).glossary
        assert reloaded is not None
        assert reloaded.content_hash == record.content_hash
        assert reloaded.term_count == 2
        assert "已啟用" in page2.lbl_glossary_status.text()

        # Real EPUB launch through the reader-facing page.
        options = _launch_epub(page2, home)
        assert options is not None
        # Canonical binding points at the Project-owned snapshot, not the user file.
        assert options.glossary_path is not None
        assert Path(options.glossary_path).resolve() != glossary_file.resolve()
        assert Path(options.glossary_path).is_file()
        assert options.glossary_hash == reloaded.content_hash

        stored = manager2.load(project.project_id)
        artifact = stored.output.artifact_path
        assert artifact and Path(artifact).is_file()
        assert stored.output.artifact_kind == "epub"
        assert stored.output.available is True
        assert Path(artifact).name.endswith("_zh.epub")

        # Fresh read-back of the persisted EPUB through a new zip handle.
        data = _read_epub(Path(artifact))
        names = data["names"]
        opf = data["opf"]
        xhtml = data["xhtml"]

        # chapter structure + identity + spine order (nav, ch1, ch2, ch3)
        for name in ("ch1.xhtml", "ch2.xhtml", "ch3.xhtml", "nav.xhtml"):
            assert any(Path(n).name == name for n in names), name
        assert _spine_idrefs(opf) == ["nav", "ch1", "ch2", "ch3"]
        # non-linear semantics preserved (ch2 supplementary)
        assert 'idref="ch2" linear="no"' in opf

        # resource mapping intact
        assert any(n.endswith("pic.png") for n in names)
        assert 'src="pic.png"' in xhtml["ch1.xhtml"]

        # production-generated glossary terminology effect in the correct chapter
        assert _TERM_A in xhtml["ch2.xhtml"]
        assert _KO_TGT in xhtml["ch2.xhtml"]
        assert _TERM_SRC not in xhtml["ch2.xhtml"]
        # no cross-chapter leakage
        assert _TERM_A not in xhtml["ch1.xhtml"]
        assert _TERM_A not in xhtml["ch3.xhtml"]
    finally:
        page2.close()


# ===========================================================================
# 2. Replace uses the new glossary through the real EPUB path
# ===========================================================================

def test_s12_07_replace_glossary_uses_new_term(qapp, tmp_path):
    home = tmp_path / "NTPE_HOME"
    manager = _manager(home)
    project = manager.create(_make_epub(tmp_path / "book.epub"), format="epub", title="Book")
    page = _page(manager)
    try:
        _select_first(page)
        _import_glossary_via_ui(page, _glossary(tmp_path, "a.txt", dst=_TERM_A, ko=False))
        record_a = manager.load(project.project_id).glossary
        assert record_a is not None
        hash_a = record_a.content_hash
        _import_glossary_via_ui(page, _glossary(tmp_path, "b.txt", dst=_TERM_B, ko=False))
        record_b = manager.load(project.project_id).glossary
        assert record_b is not None
        assert record_b.content_hash != hash_a

        options = _launch_epub(page, home)
        assert options.glossary_hash == record_b.content_hash

        stored = manager.load(project.project_id)
        artifact = stored.output.artifact_path
        assert artifact is not None
        data = _read_epub(Path(artifact))
        assert _TERM_B in data["xhtml"]["ch2.xhtml"]
        assert _TERM_A not in data["xhtml"]["ch2.xhtml"]
        assert _TERM_SRC not in data["xhtml"]["ch2.xhtml"]
    finally:
        page.close()


# ===========================================================================
# 3. Detach / no-glossary: feature-off preserved (contrast proves production effect)
# ===========================================================================

def test_s12_07_detach_then_launch_no_glossary_effect(qapp, tmp_path):
    home = tmp_path / "NTPE_HOME"
    manager = _manager(home)
    project = manager.create(_make_epub(tmp_path / "book.epub"), format="epub", title="Book")
    page = _page(manager)
    try:
        _select_first(page)
        _import_glossary_via_ui(page, _glossary(tmp_path, "g.txt"))
        with patch(_MSGBOX_QUESTION, return_value=QMessageBox.StandardButton.Yes):
            page._on_glossary_detach()
        assert manager.load(project.project_id).glossary is None

        options = _launch_epub(page, home)
        assert options.glossary_path is None
        assert options.glossary_hash is None

        artifact = manager.load(project.project_id).output.artifact_path
        assert artifact is not None
        data = _read_epub(Path(artifact))
        # no glossary -> source term survives untranslated (feature-off)
        assert _TERM_SRC in data["xhtml"]["ch2.xhtml"]
        assert _TERM_A not in data["xhtml"]["ch2.xhtml"]
    finally:
        page.close()


# ===========================================================================
# 4. Corrupt active glossary blocks the real launch
# ===========================================================================

def test_s12_07_corrupt_glossary_blocks_real_launch(qapp, tmp_path):
    home = tmp_path / "NTPE_HOME"
    manager = _manager(home)
    project = manager.create(_make_epub(tmp_path / "book.epub"), format="epub", title="Book")
    page = _page(manager)
    try:
        _select_first(page)
        _import_glossary_via_ui(page, _glossary(tmp_path, "g.txt"))
        corrupt_record = manager.load(project.project_id).glossary
        assert corrupt_record is not None and corrupt_record.stored_path is not None
        Path(corrupt_record.stored_path).unlink()

        _RealEpubRunner.captured = None
        with patch(_RUNNER, _RealEpubRunner), patch(_MSGBOX_WARNING) as warning:
            page._on_translate()
        assert _RealEpubRunner.captured is None  # adapter never invoked
        warning.assert_called_once()
    finally:
        page.close()


# ===========================================================================
# 5. Determinism of the real EPUB path
# ===========================================================================

def _structural_facts(artifact: Path) -> dict:
    data = _read_epub(artifact)
    ch2 = data["xhtml"].get("ch2.xhtml", "")
    return {
        "spine": _spine_idrefs(data["opf"]),
        "names": sorted(Path(n).name for n in data["names"] if n.endswith(".xhtml")),
        "nonlinear": 'idref="ch2" linear="no"' in data["opf"],
        "term_a": _TERM_A in ch2,
        "ko_tgt": _KO_TGT in ch2,
        "src_absent": _TERM_SRC not in ch2,
        "image": any(n.endswith("pic.png") for n in data["names"]),
    }


def test_s12_07_determinism(qapp, tmp_path):
    glossary_file = _glossary(tmp_path, "g.txt")

    facts = []
    for run in range(2):
        run_dir = tmp_path / f"run{run}"
        run_dir.mkdir()
        home = run_dir / "NTPE_HOME"
        manager = _manager(home)
        project = manager.create(_make_epub(run_dir / "book.epub"), format="epub", title="Book")
        page = _page(manager)
        try:
            _select_first(page)
            _import_glossary_via_ui(page, glossary_file)
            _launch_epub(page, home)
            artifact_path = manager.load(project.project_id).output.artifact_path
            assert artifact_path is not None
            facts.append(_structural_facts(Path(artifact_path)))
        finally:
            page.close()

    assert facts[0] == facts[1]
    assert facts[0]["term_a"] is True and facts[0]["src_absent"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
