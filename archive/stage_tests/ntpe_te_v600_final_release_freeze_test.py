from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

from core.translation_release import (
    TE_V6_FROZEN_STAGES, build_release_manifest, build_te_v6_release_contract,
    sha256_file, validate_te_v6_release,
)


FINAL_FILES = (
    "core/translation_release/__init__.py",
    "core/translation_release/te_v6_release.py",
    "core/translation_release/release_contract.py",
    "core/translation_release/release_manifest.py",
    "core/translation_release/release_validation.py",
    "ntpe_te_v600_final_release_freeze_test.py",
    "tests/integration/translation_engine_v600_final_release_freeze_test.py",
    "tests/integration/translation_engine_v600_final_import_api_test.py",
    "docs/releases/te_v6_0/TE_V6_0_FINAL_RELEASE_FREEZE.md",
)


def main() -> int:
    root = Path(__file__).resolve().parent
    assert all((root / name).is_file() for name in FINAL_FILES)
    contract = build_te_v6_release_contract()
    assert (contract.version, contract.channel, contract.frozen) == ("6.0.0", "stable", True)
    try:
        contract.version = "changed"  # type: ignore[misc]
        raise AssertionError("release contract must be immutable")
    except FrozenInstanceError:
        pass
    assert {"08.1", "10.1.1", "11.6", "12.5"}.issubset(TE_V6_FROZEN_STAGES)
    validation = validate_te_v6_release(root)
    assert validation["ready"], validation["blockers"]
    assert validation["freeze_readiness"]["ready"]
    assert validation["production_validation"]["status"] == "success"
    assert validation["network_activity"] == {"provider_client_created": False, "http_requests": 0, "nvidia_api_calls": 0}
    manifest = build_release_manifest(root, FINAL_FILES)
    assert all(item["sha256"] == sha256_file(root / item["path"]) for item in manifest["file_inventory"])
    print("TE v6.0.0 Final Release Freeze ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
