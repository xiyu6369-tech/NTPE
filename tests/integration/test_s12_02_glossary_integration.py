"""S12-02 Glossary canonical-runtime integration + recovery binding tests.

Deterministic; no provider, no network, no real translation (TXT dry-run only).
Proves the project-owned glossary reaches the canonical TXT and EPUB configuration
paths with shared semantics, and that recovery binds to the glossary identity.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.reader_project import glossary as g
from core.reader_project.manager import ReaderProjectManager
from core.reader_project.recovery import check_recovery_eligibility


def _manager(tmp_path: Path) -> ReaderProjectManager:
    return ReaderProjectManager(home=tmp_path / "NTPE_HOME")


def _source(tmp_path: Path) -> Path:
    path = tmp_path / "novel.txt"
    path.write_text("정태의는 일라이를 보았다.\n", encoding="utf-8")
    return path


def _glossary(tmp_path: Path) -> Path:
    path = tmp_path / "glossary.txt"
    path.write_text("정태의=鄭泰義\n일라이=伊萊\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# E — TXT integration
# ---------------------------------------------------------------------------

def test_project_glossary_reaches_txt_runtime(tmp_path):
    from lts.txt_translation_runtime import TxtTranslationOptions, translate_txt

    manager = _manager(tmp_path)
    home = tmp_path / "NTPE_HOME"
    source = _source(tmp_path)
    project = manager.create(source, format="txt", title="T")
    project = manager.attach_glossary(project, _glossary(tmp_path))

    options = TxtTranslationOptions(
        input_path=source, output_dir=home / "out", dry_run=True, resume=False
    )
    options = g.apply_glossary_to_options(project, options)
    assert options.glossary_path is not None
    assert options.glossary_hash == project.glossary.content_hash

    result = translate_txt(options, root=home)
    assert result["status"] in ("success", "dry_run")

    packages = sorted((home / "prompt_packages" / "txt_runtime").glob("*.json"))
    assert packages, "expected a prompt package"
    package = json.loads(packages[0].read_text(encoding="utf-8"))
    locked = package["knowledge"]["locked_dictionary"]
    assert locked.get("정태의") == "鄭泰義"
    assert locked.get("일라이") == "伊萊"


def test_feature_off_txt_has_no_glossary(tmp_path):
    from lts.txt_translation_runtime import TxtTranslationOptions, load_locked_dictionary

    manager = _manager(tmp_path)
    home = tmp_path / "NTPE_HOME"
    source = _source(tmp_path)
    project = manager.create(source, format="txt", title="T")

    options = TxtTranslationOptions(input_path=source, output_dir=home / "out")
    bound = g.apply_glossary_to_options(project, options)
    assert bound is options
    assert bound.glossary_path is None
    locked = load_locked_dictionary(home, bound)
    assert "정태의" not in locked


# ---------------------------------------------------------------------------
# F/G — EPUB integration + TXT/EPUB parity
# ---------------------------------------------------------------------------

def test_project_glossary_reaches_epub_runtime(tmp_path):
    from core.epub_translation.runtime.adapter import (
        EpubTranslationOptions,
        _apply_locked_dictionary,
        _load_locked_dictionary,
    )

    manager = _manager(tmp_path)
    home = tmp_path / "NTPE_HOME"
    source = _source(tmp_path)
    project = manager.create(source, format="txt", title="T")
    project = manager.attach_glossary(project, _glossary(tmp_path))

    options = EpubTranslationOptions(translation_input=None, chunks=())
    options = g.apply_glossary_to_options(project, options)
    assert options.glossary_path is not None
    assert options.glossary_hash == project.glossary.content_hash

    locked = _load_locked_dictionary(home, options)
    assert locked.get("정태의") == "鄭泰義"
    assert locked.get("일라이") == "伊萊"
    # Post-processing enforcement path uses the same glossary.
    assert _apply_locked_dictionary("정태의는", locked) == "鄭泰義는"


def test_txt_epub_glossary_semantics_parity(tmp_path):
    from lts.txt_translation_runtime import (
        TxtTranslationOptions,
        load_locked_dictionary,
    )
    from core.epub_translation.runtime.adapter import (
        EpubTranslationOptions,
        _load_locked_dictionary,
    )

    manager = _manager(tmp_path)
    home = tmp_path / "NTPE_HOME"
    source = _source(tmp_path)
    project = manager.create(source, format="txt", title="T")
    project = manager.attach_glossary(project, _glossary(tmp_path))

    txt_options = TxtTranslationOptions(input_path=source, output_dir=home / "out")
    epub_options = EpubTranslationOptions(translation_input=None, chunks=())
    txt_options = g.apply_glossary_to_options(project, txt_options)
    epub_options = g.apply_glossary_to_options(project, epub_options)

    txt_locked = load_locked_dictionary(home, txt_options)
    epub_locked = _load_locked_dictionary(home, epub_options)
    for key, value in {"정태의": "鄭泰義", "일라이": "伊萊"}.items():
        assert txt_locked.get(key) == value
        assert epub_locked.get(key) == value


# ---------------------------------------------------------------------------
# H — Recovery binding
# ---------------------------------------------------------------------------

def _resume(tmp_path: Path, source: Path, output_dir: Path, *, glossary_hash) -> Path:
    path = output_dir / "novel_resume_state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "chunks": {"000001": {"status": "success"}, "000002": {"status": "success"}},
        "input": str(source),
        "output_dir": str(output_dir),
    }
    if glossary_hash is not None:
        payload["glossary_hash"] = glossary_hash
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _project_with_run(tmp_path, glossary_hash):
    manager = _manager(tmp_path)
    source = _source(tmp_path)
    output_dir = tmp_path / "output"
    project = manager.create(source, format="txt", title="T")
    resume = _resume(tmp_path, source, output_dir, glossary_hash=glossary_hash)
    project.execution = type(project.execution)(
        pipeline_mode="runtime",
        session_id="s",
        resume_state_path=str(resume),
    )
    project.output = type(project.output)(
        output_dir=str(output_dir), artifact_path=None, artifact_kind=None, available=False
    )
    manager.save(project)
    return manager, project


def test_recovery_same_glossary_hash_allowed(tmp_path):
    manager, project = _project_with_run(tmp_path, glossary_hash=None)
    project = manager.attach_glossary(project, _glossary(tmp_path))
    resume = Path(project.execution.resume_state_path)
    data = json.loads(resume.read_text(encoding="utf-8"))
    data["glossary_hash"] = project.glossary.content_hash
    resume.write_text(json.dumps(data), encoding="utf-8")

    eligibility = check_recovery_eligibility(manager.load(project.project_id))
    assert eligibility.eligible is True


def test_recovery_different_glossary_hash_blocked(tmp_path):
    manager, project = _project_with_run(tmp_path, glossary_hash=None)
    project = manager.attach_glossary(project, _glossary(tmp_path))
    resume = Path(project.execution.resume_state_path)
    data = json.loads(resume.read_text(encoding="utf-8"))
    data["glossary_hash"] = "deadbeefdeadbeef"
    resume.write_text(json.dumps(data), encoding="utf-8")

    eligibility = check_recovery_eligibility(manager.load(project.project_id))
    assert eligibility.eligible is False
    assert eligibility.blocked_by == "glossary"


def test_recovery_legacy_artifact_without_hash_feature_off(tmp_path):
    manager, project = _project_with_run(tmp_path, glossary_hash=None)
    eligibility = check_recovery_eligibility(manager.load(project.project_id))
    assert eligibility.eligible is True


def test_recovery_legacy_artifact_without_hash_active_glossary_blocked(tmp_path):
    manager, project = _project_with_run(tmp_path, glossary_hash=None)
    project = manager.attach_glossary(project, _glossary(tmp_path))
    eligibility = check_recovery_eligibility(manager.load(project.project_id))
    assert eligibility.eligible is False
    assert eligibility.blocked_by == "glossary"
