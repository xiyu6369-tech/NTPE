from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import socket
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "audits/architecture_consolidation/batch2_tests"
PRODUCTION_HASH = "e33cd099619702b373488d9fd06ab6a96a1366f1d4cb89801ffbd30d0bb1ad01"


def digest(paths: list[str]) -> str:
    files: list[Path] = []
    for relative in paths:
        path = ROOT / relative
        files.extend([path] if path.is_file() else [item for item in path.rglob("*") if item.is_file()])
    result = hashlib.sha256()
    for path in sorted(files, key=lambda item: item.relative_to(ROOT).as_posix()):
        result.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        result.update(b"\0")
        result.update(hashlib.sha256(path.read_bytes()).digest())
    return result.hexdigest()


def run(path: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, path], cwd=ROOT, text=True, capture_output=True, check=False)


def test_formal_duplicate_implementation_and_legacy_command_work() -> None:
    formal = subprocess.run(
        [
            sys.executable,
            "-c",
            "import runpy; runpy.run_path('tests/integration/translation_quality_unified_nonblocking_issue_mapping_v5312_test.py', run_name='__main__')",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    legacy = run("ntpe_te_v5312_unified_nonblocking_issue_mapping_test.py")
    assert formal.returncode == legacy.returncode == 0
    assert formal.stdout == legacy.stdout
    assert "ALL PASS" in legacy.stdout


def test_consolidated_parameterized_contract_is_collectable() -> None:
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/consolidated/test_exact_duplicate_contracts.py"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "8 passed" in result.stdout


def test_deletion_inventory_and_references_are_safe() -> None:
    deletion = json.loads((AUDIT / "PROPOSED_TEST_DELETIONS.json").read_text(encoding="utf-8"))
    assert deletion["deletions"] == []
    all_python = {path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*.py")}
    all_names = {Path(path).name for path in all_python}
    pattern = re.compile(r"([A-Za-z0-9_./-]*(?:_test|test_[A-Za-z0-9_.-]*)\.py)")
    for base in (ROOT / "manifests", ROOT / "docs/releases"):
        for path in (item for item in base.rglob("*") if item.is_file()):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for reference in pattern.findall(text):
                reference = reference.lstrip("./")
                assert reference in all_python or Path(reference).name in all_names, f"dangling reference: {reference} in {path}"


def test_critical_inventory_and_production_boundary_are_unchanged() -> None:
    critical = json.loads((AUDIT / "CRITICAL_TESTS_KEEP.json").read_text(encoding="utf-8"))["tests"]
    paths = {item["path"] for item in critical}
    required = {
        "ntpe_te_v600_final_release_freeze_test.py",
        "ntpe_te_v710_stage118_translation_quality_framework_freeze_test.py",
        "ntpe_stage14_6_provider_security_test.py",
    }
    assert required <= paths
    assert all((ROOT / path).is_file() for path in paths)
    assert digest(["launcher_translate.py", "ntpe_production_translate.py"]) == PRODUCTION_HASH


def test_new_consolidation_code_cannot_open_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*args: object, **kwargs: object) -> None:
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "create_connection", blocked)
    sources = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in (
            "tests/support/compat_test_runner.py",
            "tests/consolidated/test_exact_duplicate_contracts.py",
            "ntpe_te_v5312_unified_nonblocking_issue_mapping_test.py",
        )
    )
    assert "requests." not in sources
    assert "urllib.request" not in sources
    assert "http.client" not in sources
