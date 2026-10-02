"""S10-03 — EPUB Reader-First recovery / state / isolation E2E.

Real Project persistence and the canonical S9-06 recovery contract, exercised
with EPUB sources. Runtime execution and OS opener remain injected/faked.
Provider = 0, network = 0, real translation = 0.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from core.reader_project.manager import ReaderProjectManager
from core.reader_project.models import OutputRecord
from core.reader_project.recovery import check_recovery_eligibility
from ui.translation_studio.project_view_model import build_card_model

from tests.e2e.conftest import FakeResultOpener, FakeTranslationRunner
from tests.e2e.test_s10_03_epub_reader_first_e2e import (
    make_book_epub,
    deterministic_epub_runtime,
    wait_complete,
)

_RUNNER = "ui.translation_studio.pages.project_page.TranslationRunner"
_MSGBOX = "ui.translation_studio.pages.project_page.QMessageBox"


def _chunks_ok(n: int = 4) -> dict:
    return {f"ch0001:chunk{i:04d}": {"status": "success"} for i in range(n)}


def _write_resume(path: Path, chunks: dict, input_path: Path | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict = {"chunks": chunks, "output_dir": str(path.parent)}
    if input_path is not None:
        payload["input"] = str(input_path)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _epub_project(page, tmp_path, name):
    source = make_book_epub(
        tmp_path,
        name=f"{name}.epub",
        title=name,
        identifier=f"urn:uuid:{name.lower()}",
    )
    pid = page.add_project(name=name, source=str(source), book_info={"title": name, "format": "epub"})
    assert pid is not None
    return pid, source


def _set_resume(manager, pid, resume_path, output_dir=None, artifact=None):
    project = manager.load(pid)
    project.execution.resume_state_path = str(resume_path)
    if output_dir is not None:
        project.output.output_dir = str(output_dir)
    if artifact is not None:
        project.output.artifact_path = str(artifact)
        project.output.artifact_kind = "epub"
        project.output.available = Path(artifact).is_file()
    manager.update(project, execution=project.execution, output=project.output)
    return project


# ===========================================================================
# E2E-16 — recovery eligible + resume (not fresh translation)
# ===========================================================================

def test_e2e_recovery_uses_existing_runtime_resume(qapp, tmp_path, manager, opener, page):
    pid, source = _epub_project(page, tmp_path, "Recoverable")
    out_dir = manager.store.home / "output" / pid
    resume = _write_resume(out_dir / f"{source.stem}_epub_resume_state.json", _chunks_ok(), input_path=source)
    _set_resume(manager, pid, resume, output_dir=out_dir)

    assert manager.get_recovery_blocked_reason(pid) == ("", "")
    model = build_card_model(manager.load(pid))
    assert model.recovery_eligible is True

    page.refresh_projects()
    page.table.selectRow(page._row_for_project_id(pid))
    FakeTranslationRunner.reset()
    with patch(_RUNNER, FakeTranslationRunner), patch(_MSGBOX):
        page._on_resume(pid)
    runner = FakeTranslationRunner.last()
    assert runner is not None, "recovery must start the runtime resume"
    assert getattr(runner.options, "resume", False) is True
    # the existing artifact reference is preserved (not discarded/restarted)
    assert manager.load(pid).execution.resume_state_path == str(resume)


# ===========================================================================
# E2E-17 / E2E-18 — source integrity blocks recovery
# ===========================================================================

def test_e2e_source_changed_blocks_recovery(qapp, tmp_path, manager, opener, page):
    pid, source = _epub_project(page, tmp_path, "Changed")
    out_dir = manager.store.home / "output" / pid
    resume = _write_resume(out_dir / f"{source.stem}_epub_resume_state.json", _chunks_ok())
    _set_resume(manager, pid, resume, output_dir=out_dir)
    source.write_bytes(b"changed content")

    model = build_card_model(manager.load(pid))
    assert model.recovery_eligible is False
    assert model.recovery_blocked_by == "source"


def test_e2e_source_missing_blocks_recovery(qapp, tmp_path, manager, opener, page):
    pid, source = _epub_project(page, tmp_path, "Missing")
    out_dir = manager.store.home / "output" / pid
    resume = _write_resume(out_dir / f"{source.stem}_epub_resume_state.json", _chunks_ok())
    _set_resume(manager, pid, resume, output_dir=out_dir)
    source.unlink()

    model = build_card_model(manager.load(pid))
    assert model.recovery_eligible is False
    assert model.recovery_blocked_by == "source"


# ===========================================================================
# E2E-19 — runtime artifact missing blocks, output retained
# ===========================================================================

def test_e2e_missing_runtime_artifact_blocks_output_retained(qapp, tmp_path, manager, opener, page):
    pid, source = _epub_project(page, tmp_path, "ArtifactGone")
    artifact = tmp_path / "out" / "ArtifactGone_zh.epub"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(b"EPUB")
    _set_resume(manager, pid, tmp_path / "missing_resume.json", output_dir=artifact.parent, artifact=artifact)

    model = build_card_model(manager.load(pid))
    assert model.recovery_eligible is False
    assert model.recovery_blocked_by == "artifact"
    assert model.can_open_result is True  # output ownership not cleared


# ===========================================================================
# E2E-20 / E2E-21 — wrong project / wrong source artifact blocks
# ===========================================================================

def test_e2e_wrong_project_artifact_blocks(qapp, tmp_path, manager, opener, page):
    pid_a, src_a = _epub_project(page, tmp_path, "ProjA")
    pid_b, src_b = _epub_project(page, tmp_path, "ProjB")
    dir_a = manager.store.home / "output" / pid_a
    dir_b = manager.store.home / "output" / pid_b
    resume_b = _write_resume(dir_b / f"{src_b.stem}_epub_resume_state.json", _chunks_ok(), input_path=src_b)

    # A references B's runtime artifact
    _set_resume(manager, pid_a, resume_b, output_dir=dir_a)
    # B is correctly bound and eligible
    _set_resume(manager, pid_b, resume_b, output_dir=dir_b)

    assert build_card_model(manager.load(pid_a)).recovery_eligible is False
    assert build_card_model(manager.load(pid_a)).recovery_blocked_by == "artifact"
    assert build_card_model(manager.load(pid_b)).recovery_eligible is True


def test_e2e_wrong_source_artifact_blocks(qapp, tmp_path, manager, opener, page):
    pid_a, src_a = _epub_project(page, tmp_path, "SrcA")
    pid_b, src_b = _epub_project(page, tmp_path, "SrcB")
    dir_a = manager.store.home / "output" / pid_a
    # A's runtime artifact was produced from B's source
    resume = _write_resume(dir_a / f"{src_a.stem}_epub_resume_state.json", _chunks_ok(), input_path=src_b)
    _set_resume(manager, pid_a, resume, output_dir=dir_a)

    model = build_card_model(manager.load(pid_a))
    assert model.recovery_eligible is False
    assert model.recovery_blocked_by == "artifact"


# ===========================================================================
# E2E-22 — missing output handled honestly
# ===========================================================================

def test_e2e_missing_output_not_faked(qapp, tmp_path, manager, opener, page):
    pid, source = _epub_project(page, tmp_path, "NoOutput")
    artifact = tmp_path / "out" / "NoOutput_zh.epub"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(b"EPUB")
    project = manager.load(pid)
    project.output = OutputRecord(output_dir=str(artifact.parent), artifact_path=str(artifact),
                                  artifact_kind="epub", available=True)
    manager.update(project, output=project.output)
    assert build_card_model(manager.load(pid)).can_open_result is True

    artifact.unlink()
    model = build_card_model(manager.load(pid))
    assert model.can_open_result is False
    assert model.output_note == "結果檔案不存在"
    assert model.reader_status != "completed"


# ===========================================================================
# E2E-23 — output / runtime separation (both directions)
# ===========================================================================

def test_e2e_runtime_valid_output_missing_independent(qapp, tmp_path, manager, opener, page):
    pid, source = _epub_project(page, tmp_path, "Sep1")
    dir_a = manager.store.home / "output" / pid
    resume = _write_resume(dir_a / f"{source.stem}_epub_resume_state.json", _chunks_ok(), input_path=source)
    _set_resume(manager, pid, resume, output_dir=dir_a)

    model = build_card_model(manager.load(pid))
    assert model.recovery_eligible is True
    assert model.can_open_result is False


def test_e2e_output_exists_runtime_invalid_independent(qapp, tmp_path, manager, opener, page):
    pid, source = _epub_project(page, tmp_path, "Sep2")
    artifact = tmp_path / "out" / "Sep2_zh.epub"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(b"EPUB")
    _set_resume(manager, pid, tmp_path / "missing_resume.json", output_dir=artifact.parent, artifact=artifact)

    model = build_card_model(manager.load(pid))
    assert model.can_open_result is True
    assert model.recovery_eligible is False
    assert model.recovery_blocked_by == "artifact"


# ===========================================================================
# E2E-24 — Normal Translation vs Recovery
# ===========================================================================

def test_e2e_normal_translation_allowed_recovery_blocked(qapp, tmp_path, manager, opener, page):
    pid, source = _epub_project(page, tmp_path, "Normal")
    page.table.selectRow(page._row_for_project_id(pid))

    blocked_by, _ = manager.get_recovery_blocked_reason(pid)
    assert blocked_by == "artifact"  # recovery blocked (no runtime artifact)

    # Recovery action is blocked
    FakeTranslationRunner.reset()
    with patch(_RUNNER, FakeTranslationRunner), patch(_MSGBOX):
        page._on_resume(pid)
    assert FakeTranslationRunner.last() is None

    # Normal translation is still allowed
    FakeTranslationRunner.reset()
    with patch(_RUNNER, FakeTranslationRunner), patch(_MSGBOX):
        page._on_translate()
    assert FakeTranslationRunner.last() is not None


# ===========================================================================
# E2E-25 — Project isolation
# ===========================================================================

def test_e2e_project_isolation(qapp, tmp_path, manager, opener, page):
    pid_a, src_a = _epub_project(page, tmp_path, "IsoA")
    pid_b, src_b = _epub_project(page, tmp_path, "IsoB")
    dir_a = manager.store.home / "output" / pid_a
    dir_b = manager.store.home / "output" / pid_b
    resume_a = _write_resume(dir_a / f"{src_a.stem}_epub_resume_state.json", _chunks_ok(), input_path=src_a)
    resume_b = _write_resume(dir_b / f"{src_b.stem}_epub_resume_state.json", _chunks_ok(), input_path=src_b)
    _set_resume(manager, pid_a, resume_a, output_dir=dir_a)
    _set_resume(manager, pid_b, resume_b, output_dir=dir_b)

    a = build_card_model(manager.load(pid_a))
    b = build_card_model(manager.load(pid_b))
    assert a.recovery_eligible is True and b.recovery_eligible is True
    assert manager.load(pid_a).execution.resume_state_path != manager.load(pid_b).execution.resume_state_path
    assert manager.load(pid_a).source.hash != manager.load(pid_b).source.hash


# ===========================================================================
# E2E-26 — Failure UX truthful
# ===========================================================================

def test_e2e_failure_ux_truthful(qapp, tmp_path, manager, opener, page):
    pid, source = _epub_project(page, tmp_path, "Fails")
    page.table.selectRow(page._row_for_project_id(pid))

    FakeTranslationRunner.reset()
    with patch(_RUNNER, FakeTranslationRunner), patch(_MSGBOX):
        page._on_translate()
        runner = FakeTranslationRunner.last()
        assert runner is not None
        runner.fail("deterministic failure")

    stored = manager.load(pid)
    assert stored.state.reader_status != "completed"
    assert stored.state.last_error == "翻譯失敗"
    assert stored.output.artifact_path in (None, "")
    assert build_card_model(stored).can_open_result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
