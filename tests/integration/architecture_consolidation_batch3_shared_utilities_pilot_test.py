from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.shared.evidence import sha256_file  # noqa: E402
from tools.package_audit import PackageError as AuditPackageError  # noqa: E402
from tools.package_audit import build_audit_package  # noqa: E402


SOURCE_INVENTORY_FIXTURE = ["core/tracked.py"]
AUDIT_INVENTORY_FIXTURE = ["evidence/result.txt", "evidence/結果.json"]


def _commit(root: Path, *paths: str) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "--", *paths], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.name=NTPE Test", "-c", "user.email=ntpe@example.invalid", "commit", "-qm", "fixture"],
        cwd=root,
        check=True,
    )


def _run_source(root: Path, output: Path, report: Path, *, untracked: bool = False) -> dict[str, object]:
    command = [sys.executable, str(ROOT / "tools/package_source.py"), "--root", str(root), "--output", str(output), "--report", str(report)]
    if untracked:
        command.append("--include-untracked")
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(report.read_text(encoding="utf-8"))


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts), key=lambda p: p.relative_to(root).as_posix()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def test_source_package_shared_migration_preserves_inventory_and_behavior(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    delivery = tmp_path / "delivery"
    (repo / "core").mkdir(parents=True)
    (repo / "core/tracked.py").write_text("TRACKED = True\n", encoding="utf-8")
    _commit(repo, "core/tracked.py")
    (repo / "core/untracked.py").write_text("UNTRACKED = True\n", encoding="utf-8")
    before = _tree_digest(repo)
    report = _run_source(repo, delivery / "source.zip", delivery / "source.json")
    after = _tree_digest(repo)
    with zipfile.ZipFile(delivery / "source.zip") as archive:
        assert archive.namelist() == SOURCE_INVENTORY_FIXTURE
        assert archive.testzip() is None
    assert before == after
    assert report["tracked_only"] is True and report["include_untracked"] is False
    assert {"package_type", "output", "git_head", "tracked_only", "include_untracked", "entries", "bytes", "sha256", "integrity", "path_separator_validation", "unicode_round_trip"} == set(report)
    _run_source(repo, delivery / "opt-in.zip", delivery / "opt-in.json", untracked=True)
    with zipfile.ZipFile(delivery / "opt-in.zip") as archive:
        assert archive.namelist() == ["core/tracked.py", "core/untracked.py"]


def test_source_package_invalid_git_fails_closed(tmp_path: Path) -> None:
    repo = tmp_path / "not-git"
    (repo / "core").mkdir(parents=True)
    (repo / "core/file.py").write_text("x = 1\n", encoding="utf-8")
    result = subprocess.run([sys.executable, str(ROOT / "tools/package_source.py"), "--root", str(repo), "--output", str(tmp_path / "bad.zip")], text=True, capture_output=True, check=False)
    assert result.returncode == 1
    assert not (tmp_path / "bad.zip").exists()


def test_audit_package_shared_migration_preserves_allowlist_unicode_and_report(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "evidence").mkdir(parents=True)
    (root / "evidence/result.txt").write_text("PASS\n", encoding="utf-8")
    (root / "evidence/結果.json").write_text('{"result":"PASS"}', encoding="utf-8")
    files = [{"path": path, "sha256": sha256_file(root / path)} for path in AUDIT_INVENTORY_FIXTURE]
    manifest = root / "manifest.json"
    manifest.write_text(json.dumps({"schema_version": "1.0", "files": files}, ensure_ascii=False), encoding="utf-8")
    report = build_audit_package(root, manifest, tmp_path / "audit.zip")
    with zipfile.ZipFile(tmp_path / "audit.zip") as archive:
        assert archive.namelist() == AUDIT_INVENTORY_FIXTURE
        assert archive.testzip() is None
        assert archive.getinfo("evidence/結果.json").flag_bits & 0x800
    assert {"package_type", "output", "entries", "bytes", "sha256", "manifest_validation", "integrity", "path_separator_validation", "unicode_round_trip"} == set(report)


@pytest.mark.parametrize("malicious", ["../escape.txt", "/absolute.txt", r"C:\escape.txt", ".git/config"])
def test_audit_package_rejects_malicious_allowlist_paths(tmp_path: Path, malicious: str) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "safe.txt").write_text("safe", encoding="utf-8")
    manifest = root / "manifest.json"
    manifest.write_text(json.dumps({"schema_version": "1.0", "files": [{"path": malicious, "sha256": sha256_file(root / "safe.txt")}]}), encoding="utf-8")
    with pytest.raises(AuditPackageError):
        build_audit_package(root, manifest, tmp_path / "bad.zip")


def test_audit_package_rejects_symlink_escape_and_secrets(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    secret = outside / "secret.txt"
    secret.write_bytes(b"-----BEGIN " + b"PRIVATE KEY-----")
    link = root / "linked"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except OSError as exc:
        if sys.platform != "win32":
            pytest.skip(f"symlinks unavailable: {exc}")
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], text=True, capture_output=True, check=False)
        if result.returncode != 0:
            pytest.skip(f"links unavailable: {exc}; {result.stderr}")
    manifest = root / "manifest.json"
    manifest.write_text(json.dumps({"schema_version": "1.0", "files": [{"path": "linked/secret.txt", "sha256": sha256_file(secret)}]}), encoding="utf-8")
    with pytest.raises(AuditPackageError):
        build_audit_package(root, manifest, tmp_path / "bad.zip")


def test_tooling_uses_shared_utilities_and_never_calls_provider() -> None:
    sources = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in ("tools/package_source.py", "tools/package_audit.py"))
    assert sources.count("from core.shared.evidence import") == 2
    for forbidden in ("ProviderManager", "requests.", "urllib.request", "http.client"):
        assert forbidden not in sources
