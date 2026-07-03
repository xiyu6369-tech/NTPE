from pathlib import Path

from tools.clean_project import clean_project


def make_project(root: Path) -> Path:
    root.mkdir()
    (root / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    (root / "launcher.py").write_text("print('ntpe')\n", encoding="utf-8")
    (root / "core").mkdir()
    (root / "core" / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    for dirname in ["input", "output", "translated", "cache", "logs", "sessions", ".ntpe_runtime_checkpoints"]:
        folder = root / dirname
        folder.mkdir()
        (folder / "artifact.txt").write_text("runtime artifact", encoding="utf-8")
    (root / "resume_state.json").write_text("{}", encoding="utf-8")
    (root / "translate_progress_demo.json").write_text("{}", encoding="utf-8")
    (root / "runtime.lock").write_text("1", encoding="utf-8")
    (root / "core" / "__pycache__").mkdir()
    (root / "core" / "__pycache__" / "module.pyc").write_bytes(b"cache")
    (root / "README.md").write_text("keep", encoding="utf-8")
    return root


def test_clean_project_preserves_code_and_cleans_runtime(tmp_path):
    root = make_project(tmp_path / "NTPE")

    result = clean_project(root, dry_run=False)

    assert (root / "core" / "module.py").exists()
    assert (root / "README.md").exists()
    assert not (root / "resume_state.json").exists()
    assert not (root / "translate_progress_demo.json").exists()
    assert not (root / "runtime.lock").exists()
    assert (root / "input" / ".gitkeep").exists()
    assert not (root / "input" / "artifact.txt").exists()
    assert not (root / "core" / "__pycache__").exists()
    assert "input" in result.cleaned_dirs


def test_clean_project_dry_run_does_not_delete(tmp_path):
    root = make_project(tmp_path / "NTPE")

    result = clean_project(root, dry_run=True)

    assert (root / "input" / "artifact.txt").exists()
    assert (root / "resume_state.json").exists()
    assert (root / "core" / "__pycache__").exists()
    assert result.dry_run is True
    assert "input" in result.cleaned_dirs
