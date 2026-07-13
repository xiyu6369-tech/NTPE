from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable
from zipfile import ZIP_DEFLATED, ZipFile

from .release_validation import validate_te_v6_release
from .te_v6_release import (EVIDENCE_INVARIANTS, NATURALNESS_INVARIANTS, PROMPT_INVARIANTS,
                            PROVIDER_INVARIANTS, QUALITY_INVARIANTS, RETRY_INVARIANTS,
                            TE_V6_FROZEN_STAGES)


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_release_manifest(project_root: str | Path, files: Iterable[str]) -> dict[str, object]:
    root = Path(project_root).resolve()
    validation = validate_te_v6_release(root)
    if not validation["ready"]:
        raise RuntimeError(f"TE v6.0 release is not ready: {validation['blockers']}")
    inventory = [{"path": name, "sha256": sha256_file(root / name)} for name in sorted(set(files))]
    return {
        "version": "6.0.0", "release_channel": "stable", "frozen": True,
        "frozen_stages": list(TE_V6_FROZEN_STAGES),
        "public_apis": ["TEV6ReleaseContract", "build_te_v6_release_contract", "validate_te_v6_release"],
        "provider_invariants": list(PROVIDER_INVARIANTS), "prompt_invariants": list(PROMPT_INVARIANTS),
        "quality_invariants": list(QUALITY_INVARIANTS), "retry_invariants": list(RETRY_INVARIANTS),
        "evidence_invariants": list(EVIDENCE_INVARIANTS), "naturalness_invariants": list(NATURALNESS_INVARIANTS),
        "production_validation": validation["production_validation"],
        "freeze_readiness": {"ready": True, "blockers": []},
        "validation_commands": ["python ntpe_te_v600_final_release_freeze_test.py", "python -m pytest -q tests/integration/translation_engine_v600_final_release_freeze_test.py tests/integration/translation_engine_v600_final_import_api_test.py", "python ntpe_validate.py", "git diff --check"],
        "file_inventory": inventory, "git_commit": "<pending>", "tag": "<pending: te-v6.0.0>",
    }


def write_release_manifest(project_root: str | Path, files: Iterable[str], output: str | Path) -> dict[str, object]:
    payload = build_release_manifest(project_root, files)
    Path(output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def write_delta_zip(project_root: str | Path, files: Iterable[str], output: str | Path) -> None:
    root = Path(project_root).resolve()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name in sorted(set(files)):
            archive.write(root / name, name)
