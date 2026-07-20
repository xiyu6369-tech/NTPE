from __future__ import annotations

from pathlib import Path as _NtpeVerificationPath

_ntpe_verification_root = next(
    parent for parent in _NtpeVerificationPath(__file__).resolve().parents if parent.name == "verification"
)
exec((_ntpe_verification_root / "_bootstrap.py").read_text(encoding="utf-8"), globals())
activate_verification(_ntpe_verification_root)

import json

from tools.audit_project_layout import build_inventory


ARTIFACT_DIR = verification_project_root() / "artifacts/ntpe_v20_stage0_project_layout_consolidation"


def _load(name: str) -> dict:
    return json.loads((ARTIFACT_DIR / name).read_text(encoding="utf-8"))


def test_stage0_project_layout_consolidation() -> None:
    root = verification_project_root()
    inventory = build_inventory()
    initial = _load("INITIAL_ROOT_INVENTORY.json")
    final = _load("FINAL_ROOT_INVENTORY.json")
    move_map = _load("MOVE_MAP.json")
    retained = _load("RETAINED_ROOT_WRAPPERS.json")
    compatibility = _load("COMPATIBILITY_WRAPPERS.json")
    excluded = _load("EXCLUDED_TRACKED_FILES.json")

    assert inventory["unexpected_root_files"] == []
    assert inventory["unexpected_root_directories"] == []
    assert initial["root_total_files"] == 424
    assert initial["root_python_files"] == 339
    assert final["root_total_files"] == inventory["root_total_files"]
    assert final["root_python_files"] == 339
    assert move_map["move_count"] == 76
    assert len({item["source"] for item in move_map["moves"]}) == 76
    assert len({item["destination"] for item in move_map["moves"]}) == 76
    assert retained["count"] == len(inventory["historical_wrappers"])
    assert compatibility["created_count"] == 0
    assert excluded["total_count"] == 370
    assert excluded["head_match"] is True
    assert excluded["tracked_diff_files"] == []
    assert (root / "docs/PROJECT_LAYOUT.md").is_file()
    assert (root / "config/project_layout_policy.json").is_file()
    assert (root / "tools/audit_project_layout.py").is_file()


if __name__ == "__main__":
    test_stage0_project_layout_consolidation()
    print("NTPE_V20_STAGE0_PROJECT_LAYOUT_CONSOLIDATION=PASS")
