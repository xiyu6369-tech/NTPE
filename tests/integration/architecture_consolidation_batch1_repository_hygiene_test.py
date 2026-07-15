from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.package_audit import PackageError as AuditPackageError  # noqa: E402
from tools.package_audit import build_audit_package, sha256_file  # noqa: E402


def _run_source(
    root: Path,
    output: Path,
    report: Path,
    *,
    include_untracked: bool = False,
) -> dict[str, object]:
    command = [
        sys.executable,
        str(ROOT / "tools/package_source.py"),
        "--root",
        str(root),
        "--output",
        str(output),
        "--report",
        str(report),
    ]
    if include_untracked:
        command.append("--include-untracked")
    result = subprocess.run(
        command,
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(report.read_text(encoding="utf-8"))


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(
        (
            item
            for item in root.rglob("*")
            if item.is_file() and ".git" not in item.relative_to(root).parts
        ),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _commit(root: Path, *paths: str) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "--", *paths], cwd=root, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=NTPE Test",
            "-c",
            "user.email=ntpe-test@example.invalid",
            "commit",
            "-qm",
            "tracked source fixture",
        ],
        cwd=root,
        check=True,
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, text=True, capture_output=True
    ).stdout.strip()


def test_source_package_defaults_to_tracked_only_and_opt_in_is_explicit(tmp_path: Path) -> None:
    worktree = tmp_path / "repo"
    outside = tmp_path / "delivery"
    (worktree / "core").mkdir(parents=True)
    (worktree / "core/tracked.py").write_text("TRACKED = True\n", encoding="utf-8")
    git_head = _commit(worktree, "core/tracked.py")
    (worktree / "core/local_experiment.py").write_text("LOCAL = True\n", encoding="utf-8")
    before = _tree_digest(worktree)
    result = _run_source(worktree, outside / "source.zip", outside / "source-report.json")
    after = _tree_digest(worktree)

    assert before == after
    assert result["git_head"] == git_head
    assert result["tracked_only"] is True
    assert result["include_untracked"] is False
    assert result["integrity"] == result["path_separator_validation"] == result["unicode_round_trip"] == "PASS"
    with zipfile.ZipFile(outside / "source.zip") as archive:
        assert archive.namelist() == ["core/tracked.py"]
        assert archive.testzip() is None
        assert all("\\" not in name for name in archive.namelist())

    opt_in = _run_source(
        worktree,
        outside / "source-with-untracked.zip",
        outside / "source-with-untracked-report.json",
        include_untracked=True,
    )
    assert opt_in["git_head"] == git_head
    assert opt_in["tracked_only"] is False
    assert opt_in["include_untracked"] is True
    with zipfile.ZipFile(outside / "source-with-untracked.zip") as archive:
        assert archive.namelist() == ["core/local_experiment.py", "core/tracked.py"]


def test_source_package_unicode_tracked_filename_round_trips(tmp_path: Path) -> None:
    worktree = tmp_path / "unicode-repo"
    (worktree / "docs/architecture").mkdir(parents=True)
    path = worktree / "docs/architecture/繁體中文.md"
    path.write_text("可攜式封裝\n", encoding="utf-8")
    _commit(worktree, "docs/architecture/繁體中文.md")
    _run_source(worktree, tmp_path / "unicode.zip", tmp_path / "unicode-report.json")
    with zipfile.ZipFile(tmp_path / "unicode.zip") as archive:
        assert archive.namelist() == ["docs/architecture/繁體中文.md"]
        assert archive.getinfo("docs/architecture/繁體中文.md").flag_bits & 0x800


def test_source_package_fails_closed_without_git_head(tmp_path: Path) -> None:
    worktree = tmp_path / "repo-without-head"
    (worktree / "core").mkdir(parents=True)
    (worktree / "core/tracked.py").write_text("TRACKED = True\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=worktree, check=True)
    subprocess.run(["git", "add", "core/tracked.py"], cwd=worktree, check=True)
    output = tmp_path / "must-not-exist.zip"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/package_source.py"),
            "--root",
            str(worktree),
            "--output",
            str(output),
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 1
    assert "Git HEAD" in result.stderr
    assert not output.exists()


def test_audit_package_uses_only_validated_manifest_entries(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "evidence").mkdir(parents=True)
    (root / "evidence/result.txt").write_text("PASS\n", encoding="utf-8")
    (root / "evidence/結果.json").write_text('{"result":"PASS"}\n', encoding="utf-8")
    entries = [
        {"path": "evidence/result.txt", "sha256": sha256_file(root / "evidence/result.txt")},
        {"path": "evidence/結果.json", "sha256": sha256_file(root / "evidence/結果.json")},
    ]
    manifest = root / "manifest.json"
    manifest.write_text(json.dumps({"schema_version": "1.0", "files": entries}, ensure_ascii=False), encoding="utf-8")
    result = build_audit_package(root, manifest, tmp_path / "audit.zip")
    assert result["entries"] == 2
    assert result["manifest_validation"] == result["integrity"] == "PASS"
    with zipfile.ZipFile(tmp_path / "audit.zip") as archive:
        assert archive.namelist() == ["evidence/result.txt", "evidence/結果.json"]


@pytest.mark.parametrize(
    "path,content",
    [
        ("../escape.txt", b"x"),
        (".git/config", b"x"),
        ("evidence/private.txt", b"-----BEGIN " + b"PRIVATE KEY-----"),
        ("evidence/archive.zip", b"x"),
    ],
)
def test_audit_package_rejects_forbidden_entries(tmp_path: Path, path: str, content: bytes) -> None:
    root = tmp_path / "repo"
    safe = root / "evidence/private.txt"
    safe.parent.mkdir(parents=True)
    safe.write_bytes(content)
    manifest = root / "manifest.json"
    manifest.write_text(
        json.dumps({"schema_version": "1.0", "files": [{"path": path, "sha256": hashlib.sha256(content).hexdigest()}]}),
        encoding="utf-8",
    )
    with pytest.raises(AuditPackageError):
        build_audit_package(root, manifest, tmp_path / "audit.zip")


def test_packagers_have_no_network_or_provider_execution() -> None:
    combined = "\n".join(
        (ROOT / relative).read_text(encoding="utf-8")
        for relative in ("tools/package_source.py", "tools/package_audit.py")
    )
    assert "urllib.request" not in combined
    assert "http.client" not in combined
    assert "requests." not in combined
    assert "ProviderManager" not in combined
