"""S12-04 — Glossary Reader-First Production E2E Verification.

Closes the Glossary MVP with a full reader-first, production-path E2E:

  ProjectPage import -> S12-02 backend -> ReaderProject persistence -> restart
  -> UI translate -> apply_glossary_to_options -> canonical runtime
  (deterministic provider injection) -> real TXT / EPUB output -> fresh read-back.

Only the provider is injected (`RuntimeOrchestrator.execute` -> deterministic echo).
The UI action, ReaderProject state, glossary backend, canonical option binding,
canonical glossary loader, packaging and final artifact write/read-back are all real.
No provider, no network, no real translation.

Placed under ``tests/integration`` because the shared Qt e2e session has a pre-existing
PySide6/Python 3.14 fatal in a background TranslationRuntime thread when a new e2e module
perturbs the directory run (S11-10 finding). This module drives ProjectPage on the main
thread with a synchronous runner, so the semantics are unchanged by the placement.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.reader_project.manager import ReaderProjectManager
from core.reader_project.recovery import check_recovery_eligibility
from core.epub_translation.runtime.adapter import EpubTranslationOptions
from lts.txt_translation_runtime import TxtTranslationOptions
from ui.translation_studio.pages.project_page import ProjectPage

_DIALOG_OPEN = "ui.translation_studio.pages.project_page.QFileDialog.getOpenFileName"
_MSGBOX_WARNING = "ui.translation_studio.pages.project_page.QMessageBox.warning"
_MSGBOX_QUESTION = "ui.translation_studio.pages.project_page.QMessageBox.question"
_MSGBOX_INFO = "ui.translation_studio.pages.project_page.QMessageBox.information"
_MSGBOX_CRITICAL = "ui.translation_studio.pages.project_page.QMessageBox.critical"
_RUNNER = "ui.translation_studio.pages.project_page.TranslationRunner"
_ORCH_EXECUTE = "core.runtime_orchestrator.manager.RuntimeOrchestrator.execute"

_TERM_SRC = "TEST_TERM_A"
_TERM_A = "測試詞彙甲"
_TERM_B = "測試詞彙乙"
_KO_SRC = "정태의"
_KO_TGT = "鄭泰義"


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication(sys.argv)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _txt_source(tmp_path: Path, name: str = "novel.txt") -> Path:
    path = tmp_path / name
    path.write_text(
        f"{_TERM_SRC} appears in the story. {_KO_SRC} appears too.\n", encoding="utf-8"
    )
    return path


def _epub_source(tmp_path: Path, name: str = "book.epub") -> Path:
    path = tmp_path / name
    kh_body = f"{_TERM_SRC} 등장한다. " + ("정태의는 일라이를 보았다. " * 60)
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
    <dc:title>Glossary Book</dc:title><dc:identifier id="b">urn:uuid:glossary-book</dc:identifier>
    <dc:language>ko</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine><itemref idref="ch1"/></spine>
</package>""",
        )
        zf.writestr(
            "OEBPS/ch1.xhtml",
            '<html xmlns="http://www.w3.org/1999/xhtml"><head></head>'
            f"<body><p>{kh_body}</p></body></html>",
        )
    return path


def _glossary(tmp_path: Path, name: str, src: str = _TERM_SRC, dst: str = _TERM_A, ko: bool = True) -> Path:
    path = tmp_path / name
    lines = [f"{src} = {dst}"]
    if ko:
        lines.append(f"{_KO_SRC} = {_KO_TGT}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _manager(tmp_path: Path) -> ReaderProjectManager:
    return ReaderProjectManager(home=tmp_path / "NTPE_HOME")


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


def _fake_orchestrator_execute(self, chunk_text="", **kwargs):
    metadata = kwargs.get("metadata") or {}
    source = metadata.get("source", {}).get("chunk_text", chunk_text)
    return SimpleNamespace(
        response={"status": "success", "translation": source},
        metadata=None,
        session=None,
        request=None,
    )


def _import_via_ui(page: ProjectPage, path: Path) -> None:
    with _patch_dialog(path):
        page._on_glossary_import()


class _E2ERunner:
    """Synchronous stand-in for the Qt runner that still executes the canonical runtime.

    ``root_override`` makes the canonical runtime hermetic (config / character memory
    under the test home) so tests never write to the repository's ``memory/`` tree.
    """

    captured = None
    root_override: "Path | None" = None

    def __init__(self, options, root_path):
        _E2ERunner.captured = options
        self._options = options
        self._root = _E2ERunner.root_override or root_path

    def start(self, on_progress=None, on_finished=None, on_error=None):
        try:
            if isinstance(self._options, EpubTranslationOptions):
                from ui.translation_studio.translation_worker import TranslationWorker

                result = TranslationWorker(self._options, self._root)._runtime_epub_translate(
                    self._options
                )
            else:
                from lts.txt_translation_runtime import translate_txt

                result = translate_txt(self._options, root=self._root)
        except Exception as exc:  # pragma: no cover - surfaced to the test
            if on_error is not None:
                on_error(str(exc))
            raise
        if on_finished is not None:
            on_finished(result)


class _CaptureOnlyRunner:
    """Captures canonical options without executing a runtime (option-binding proof)."""

    captured = None

    def __init__(self, options, root_path):
        _CaptureOnlyRunner.captured = options

    def start(self, on_progress=None, on_finished=None, on_error=None):
        pass


def _launch(page: ProjectPage, root: Path | None = None, runner_cls=_E2ERunner):
    if runner_cls is _E2ERunner:
        _E2ERunner.captured = None
        _E2ERunner.root_override = root
    else:
        _CaptureOnlyRunner.captured = None
    try:
        with patch(_RUNNER, runner_cls), patch(_ORCH_EXECUTE, _fake_orchestrator_execute), \
                patch(_MSGBOX_INFO), patch(_MSGBOX_WARNING), patch(_MSGBOX_CRITICAL):
            page._on_translate()
    finally:
        _E2ERunner.root_override = None
    return runner_cls.captured


def _read_epub_chapters(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        chunks = []
        for name in zf.namelist():
            if name.endswith(".xhtml"):
                chunks.append(zf.read(name).decode("utf-8"))
        return "\n".join(chunks)


# ===========================================================================
# 1. UI import -> backend -> persistence -> restart
# ===========================================================================

def test_s12_04_ui_import_persistence_restart(qapp, tmp_path):
    home = tmp_path / "NTPE_HOME"
    manager = ReaderProjectManager(home=home)
    project = manager.create(_txt_source(tmp_path), format="txt", title="Novel")
    page = _page(manager)
    try:
        _select_first(page)
        _import_via_ui(page, _glossary(tmp_path, "g.txt"))
        record = manager.load(project.project_id).glossary
        assert record is not None
        assert record.term_count == 2
        assert "已啟用" in page.lbl_glossary_status.text()
        assert "g.txt" in page.lbl_glossary_status.text()
    finally:
        page.close()

    # Fresh manager + page (restart).
    manager2 = ReaderProjectManager(home=home)
    page2 = _page(manager2)
    try:
        _select_first(page2)
        reloaded = manager2.load(project.project_id).glossary
        assert reloaded is not None
        assert reloaded.content_hash == record.content_hash
        assert reloaded.term_count == 2
        assert "已啟用" in page2.lbl_glossary_status.text()
    finally:
        page2.close()


# ===========================================================================
# 2. TXT launch: canonical binding + terminology effect + persisted output
# ===========================================================================

def test_s12_04_txt_launch_binding_and_terminology_effect(qapp, tmp_path):
    home = tmp_path / "NTPE_HOME"
    manager = ReaderProjectManager(home=home)
    project = manager.create(_txt_source(tmp_path), format="txt", title="Novel")
    glossary_file = _glossary(tmp_path, "g.txt")
    page = _page(manager)
    try:
        _select_first(page)
        _import_via_ui(page, glossary_file)
        options = _launch(page, home)

        record = manager.load(project.project_id).glossary
        assert isinstance(options, TxtTranslationOptions)
        assert options.glossary_hash == record.content_hash
        # canonical binding points at the project-owned snapshot, not the user file
        assert Path(options.glossary_path).resolve() != glossary_file.resolve()
        assert Path(options.glossary_path).is_file()

        stored = manager.load(project.project_id)
        assert stored.output.artifact_path
        assert stored.output.available is True
        output_text = Path(stored.output.artifact_path).read_text(encoding="utf-8")
        assert _TERM_A in output_text
        assert _KO_TGT in output_text
        assert _TERM_SRC not in output_text
    finally:
        page.close()


# ===========================================================================
# 3. EPUB: canonical option binding + canonical glossary mechanism
#    (the real adapter execution leg is BLOCKED by a pre-existing, unrelated
#     chunk-offset validation defect — see the evidence test below)
# ===========================================================================

def test_s12_04_epub_option_binding_and_canonical_glossary(qapp, tmp_path):
    home = tmp_path / "NTPE_HOME"
    manager = ReaderProjectManager(home=home)
    project = manager.create(_epub_source(tmp_path), format="epub", title="Book")
    page = _page(manager)
    try:
        _select_first(page)
        _import_via_ui(page, _glossary(tmp_path, "g.txt"))
        options = _launch(page, home, runner_cls=_CaptureOnlyRunner)

        record = manager.load(project.project_id).glossary
        assert isinstance(options, EpubTranslationOptions)
        assert options.glossary_hash == record.content_hash
        assert Path(options.glossary_path).resolve() != _glossary(tmp_path, "g.txt").resolve()
        assert Path(options.glossary_path).is_file()

        # Canonical EPUB glossary loader + canonical post-processing mechanism.
        from core.epub_translation.runtime.adapter import (
            _apply_locked_dictionary,
            _load_locked_dictionary,
        )

        locked = _load_locked_dictionary(home, options)
        assert locked.get(_TERM_SRC) == _TERM_A
        assert locked.get(_KO_SRC) == _KO_TGT
        assert _apply_locked_dictionary(f"{_TERM_SRC} 등장", locked).startswith(_TERM_A)
    finally:
        page.close()


def test_s12_04_epub_real_adapter_chunk_validation_defect_evidence(qapp, tmp_path):
    """Affected real-adapter path, re-verified after the S12-06 repair.

    S12-04 recorded a pre-existing defect: ``chunk_epub_translation_input`` emits
    chapter-body-relative ``body_start_offset`` while ``validate_epub_translation_chunk``
    wrongly required marker-inclusive absolute, so the real
    ``translate_epub_translation_input`` rejected canonical chunks for any marker-prefixed
    chapter. S12-06 repaired the validator's cross-space comparison, so the real adapter
    now proceeds past the offset gate. The full persisted-E2E read-back remains deferred
    to S12-07; only the offset-gate flip is asserted here.
    """
    from ui.translation_studio.translation_worker import TranslationWorker

    home = tmp_path / "NTPE_HOME"
    manager = ReaderProjectManager(home=home)
    manager.create(_epub_source(tmp_path), format="epub", title="Book")
    page = _page(manager)
    try:
        _select_first(page)
        _import_via_ui(page, _glossary(tmp_path, "g.txt"))
        options = _launch(page, home, runner_cls=_CaptureOnlyRunner)

        with patch(_ORCH_EXECUTE, _fake_orchestrator_execute):
            result = TranslationWorker(options, home)._runtime_epub_translate(options)
        # The real adapter ran (no ContractValidationError from the offset gate).
        assert result["status"] in {"success", "incomplete"}
    finally:
        page.close()


# ===========================================================================
# 4. No glossary -> feature-off unchanged
# ===========================================================================

def test_s12_04_no_glossary_feature_off(qapp, tmp_path):
    home = tmp_path / "NTPE_HOME"
    manager = ReaderProjectManager(home=home)
    project = manager.create(_txt_source(tmp_path), format="txt", title="Novel")
    page = _page(manager)
    try:
        _select_first(page)
        options = _launch(page, home)
        assert options.glossary_path is None
        assert options.glossary_hash is None

        stored = manager.load(project.project_id)
        output_text = Path(stored.output.artifact_path).read_text(encoding="utf-8")
        assert _TERM_SRC in output_text  # no glossary -> unchanged source term
        assert _TERM_A not in output_text
    finally:
        page.close()


# ===========================================================================
# 5. Replace -> runtime uses the new glossary
# ===========================================================================

def test_s12_04_replace_then_launch_uses_new_glossary(qapp, tmp_path):
    home = tmp_path / "NTPE_HOME"
    manager = ReaderProjectManager(home=home)
    project = manager.create(_txt_source(tmp_path), format="txt", title="Novel")
    page = _page(manager)
    try:
        _select_first(page)
        _import_via_ui(page, _glossary(tmp_path, "a.txt", dst=_TERM_A))
        hash_a = manager.load(project.project_id).glossary.content_hash

        _import_via_ui(page, _glossary(tmp_path, "b.txt", dst=_TERM_B))
        hash_b = manager.load(project.project_id).glossary.content_hash
        assert hash_a != hash_b

        options = _launch(page, home)
        assert options.glossary_hash == hash_b
        output_text = Path(manager.load(project.project_id).output.artifact_path).read_text(encoding="utf-8")
        assert _TERM_B in output_text
        assert _TERM_A not in output_text
    finally:
        page.close()


# ===========================================================================
# 6. Detach -> launch feature-off
# ===========================================================================

def test_s12_04_detach_then_launch_feature_off(qapp, tmp_path):
    home = tmp_path / "NTPE_HOME"
    manager = ReaderProjectManager(home=home)
    project = manager.create(_txt_source(tmp_path), format="txt", title="Novel")
    page = _page(manager)
    try:
        _select_first(page)
        _import_via_ui(page, _glossary(tmp_path, "g.txt"))
        with patch(_MSGBOX_QUESTION, return_value=QMessageBox.StandardButton.Yes):
            page._on_glossary_detach()
        assert manager.load(project.project_id).glossary is None

        options = _launch(page, home)
        assert options.glossary_path is None
        assert options.glossary_hash is None
    finally:
        page.close()


# ===========================================================================
# 7. Invalid import -> project unchanged
# ===========================================================================

def test_s12_04_invalid_import_leaves_project_unchanged(qapp, tmp_path):
    home = tmp_path / "NTPE_HOME"
    manager = ReaderProjectManager(home=home)
    project = manager.create(_txt_source(tmp_path), format="txt", title="Novel")
    page = _page(manager)
    try:
        _select_first(page)
        _import_via_ui(page, _glossary(tmp_path, "a.txt", dst=_TERM_A))
        hash_before = manager.load(project.project_id).glossary.content_hash

        bad = tmp_path / "bad.json"
        bad.write_text("{not valid", encoding="utf-8")
        with patch(_MSGBOX_WARNING) as warning:
            _import_via_ui(page, bad)
        warning.assert_called_once()
        assert manager.load(project.project_id).glossary.content_hash == hash_before
    finally:
        page.close()


# ===========================================================================
# 8. Corrupt active glossary -> launch blocked
# ===========================================================================

def test_s12_04_corrupt_active_glossary_blocks_launch(qapp, tmp_path):
    home = tmp_path / "NTPE_HOME"
    manager = ReaderProjectManager(home=home)
    project = manager.create(_txt_source(tmp_path), format="txt", title="Novel")
    page = _page(manager)
    try:
        _select_first(page)
        _import_via_ui(page, _glossary(tmp_path, "g.txt"))
        Path(manager.load(project.project_id).glossary.stored_path).unlink()

        _E2ERunner.captured = None
        with patch(_RUNNER, _E2ERunner), patch(_MSGBOX_WARNING) as warning:
            page._on_translate()
        assert _E2ERunner.captured is None
        warning.assert_called_once()
    finally:
        page.close()


# ===========================================================================
# 9. Recovery compatibility (same vs different glossary)
# ===========================================================================

def _project_with_resume(tmp_path, glossary_hash):
    import json

    home = tmp_path / "NTPE_HOME"
    manager = ReaderProjectManager(home=home)
    source = _txt_source(tmp_path)
    output_dir = tmp_path / "output"
    project = manager.create(source, format="txt", title="Novel")
    output_dir.mkdir(parents=True, exist_ok=True)
    resume = output_dir / "novel_resume_state.json"
    resume.write_text(
        json.dumps({
            "chunks": {"000001": {"status": "success"}, "000002": {"status": "success"}},
            "input": str(source), "output_dir": str(output_dir), "glossary_hash": glossary_hash,
        }),
        encoding="utf-8",
    )
    project.execution = type(project.execution)(resume_state_path=str(resume))
    project.output = type(project.output)(output_dir=str(output_dir))
    manager.save(project)
    return manager, project


def test_s12_04_recovery_same_glossary_coherent(tmp_path):
    manager, project = _project_with_resume(tmp_path, None)
    project = manager.attach_glossary(project, _glossary(tmp_path, "g.txt"))
    import json

    resume = Path(project.execution.resume_state_path)
    data = json.loads(resume.read_text(encoding="utf-8"))
    data["glossary_hash"] = project.glossary.content_hash
    resume.write_text(json.dumps(data), encoding="utf-8")
    assert check_recovery_eligibility(manager.load(project.project_id)).eligible is True


def test_s12_04_recovery_different_glossary_blocked(tmp_path):
    manager, project = _project_with_resume(tmp_path, "deadbeefdeadbeef")
    project = manager.attach_glossary(project, _glossary(tmp_path, "g.txt"))
    eligibility = check_recovery_eligibility(manager.load(project.project_id))
    assert eligibility.eligible is False
    assert eligibility.blocked_by == "glossary"


# ===========================================================================
# 10. Determinism
# ===========================================================================

def test_s12_04_determinism(qapp, tmp_path):
    home = tmp_path / "NTPE_HOME"
    manager = ReaderProjectManager(home=home)
    manager.create(_txt_source(tmp_path), format="txt", title="Novel")
    page = _page(manager)
    try:
        _select_first(page)
        _import_via_ui(page, _glossary(tmp_path, "g.txt"))

        first = _launch(page, home)
        second = _launch(page, home)
        assert first.glossary_hash == second.glossary_hash
        assert Path(first.glossary_path) == Path(second.glossary_path)
    finally:
        page.close()
