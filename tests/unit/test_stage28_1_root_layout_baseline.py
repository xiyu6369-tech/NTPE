from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from tools import audit_project_layout
from tools.audit_project_layout import build_inventory


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config" / "project_layout_policy.json"
EXPECTED_FILES = (".clineignore", ".clinerules", ".editorconfig")
EXPECTED_DIRECTORIES = (".ai",)


def _policy() -> dict[str, object]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _write_policy(tmp_path: Path, policy: dict[str, object]) -> Path:
    policy_path = tmp_path.parent / f"{tmp_path.name}_policy.json"
    policy_path.write_text(
        json.dumps(policy, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return policy_path


def test_tracked_metadata_baseline_is_explicitly_allowed(tmp_path: Path) -> None:
    for name in EXPECTED_FILES:
        (tmp_path / name).write_text("metadata", encoding="utf-8")
    for name in EXPECTED_DIRECTORIES:
        (tmp_path / name).mkdir()

    inventory = build_inventory(tmp_path, _write_policy(tmp_path, _policy()))

    assert inventory["unexpected_root_files"] == []
    assert inventory["unexpected_root_directories"] == []


@pytest.mark.parametrize(
    "name",
    ("unexpected_tool_config", ".random_hidden_file", "debug_dump.json"),
)
def test_unknown_root_file_is_rejected(tmp_path: Path, name: str) -> None:
    (tmp_path / name).write_text("unexpected", encoding="utf-8")
    inventory = build_inventory(tmp_path, _write_policy(tmp_path, _policy()))
    assert inventory["unexpected_root_files"] == [name]


def test_unknown_root_directory_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "unknown_root_directory").mkdir()
    inventory = build_inventory(tmp_path, _write_policy(tmp_path, _policy()))
    assert inventory["unexpected_root_directories"] == ["unknown_root_directory"]


def test_unknown_root_python_script_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "temporary_script.py").write_text("pass\n", encoding="utf-8")
    inventory = build_inventory(tmp_path, _write_policy(tmp_path, _policy()))
    assert inventory["unexpected_root_files"] == ["temporary_script.py"]


def test_allowlists_are_exact_unique_and_deterministic(tmp_path: Path) -> None:
    policy = _policy()
    allowed_files = policy["allowed_root_files"]
    allowed_directories = policy["allowed_root_directories"]

    assert all(allowed_files.count(name) == 1 for name in EXPECTED_FILES)
    assert all(allowed_directories.count(name) == 1 for name in EXPECTED_DIRECTORIES)
    assert len(allowed_files) == len(set(allowed_files))
    assert len(allowed_directories) == len(set(allowed_directories))
    assert not any("*" in name for name in (*allowed_files, *allowed_directories))

    policy_path = _write_policy(tmp_path, policy)
    first = build_inventory(tmp_path, policy_path)
    second = build_inventory(tmp_path, policy_path)
    assert first == second


def test_existing_legal_root_items_remain_allowed(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("NTPE", encoding="utf-8")
    (tmp_path / "core").mkdir()
    inventory = build_inventory(tmp_path, _write_policy(tmp_path, _policy()))
    assert inventory["unexpected_root_files"] == []
    assert inventory["unexpected_root_directories"] == []


def test_layout_audit_has_no_execution_dependency() -> None:
    source = inspect.getsource(audit_project_layout).lower()
    forbidden = (
        "import requests",
        "import urllib",
        "import socket",
        "provider.invoke(",
        "translate(",
    )
    assert not any(token in source for token in forbidden)
