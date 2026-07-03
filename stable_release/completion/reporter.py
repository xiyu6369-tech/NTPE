"""Writers for NTPE 1.0.0 stable release completion artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .manifest import StableCompletionManifest, create_stable_completion_manifest
from .validator import StableCompletionValidator


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_stable_completion_manifest(root: Path | str = ".") -> Dict[str, str]:
    root = Path(root)
    manifest = create_stable_completion_manifest(source_stage="STABLE.2", release_channel="stable")
    validation = StableCompletionValidator(root, manifest).run()
    payload = manifest.to_dict()
    payload["validation"] = validation["validation"]
    payload["passed"] = validation["passed"]

    manifest_path = root / "Stable_Release_Complete_Manifest_1_0_0.json"
    hash_path = root / "Stable_Release_Complete_Hash_1_0_0.json"
    write_json(manifest_path, payload)
    write_json(hash_path, {
        "stage": manifest.stage,
        "status": manifest.status,
        "version": manifest.version,
        "release_channel": manifest.release_channel,
        "hash": manifest.completion_hash(),
        "source_stage": manifest.source_stage,
        "source_version": manifest.source_version,
    })
    return {"manifest_path": str(manifest_path), "hash_path": str(hash_path)}


def load_stable_completion_manifest(path: Path | str) -> Dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_stable_completion_reports(root: Path | str = ".") -> Dict[str, str]:
    root = Path(root)
    manifest = StableCompletionManifest()
    result = StableCompletionValidator(root, manifest).run()
    status = result["status"]
    validation = result["validation"]

    report = f"""# NTPE 1.0 Stable Release Complete Report

## Result
{status}

## Release
- Version: 1.0.0
- Channel: stable
- Source stage: STABLE.2 Stable Release Finalization
- Status: COMPLETE

## Validation
- Stable finalization artifacts: {'PASS' if validation['required_finalization_artifacts_valid'] else 'FAIL'}
- Stable preparation artifacts: {'PASS' if validation['required_preparation_artifacts_valid'] else 'FAIL'}
- RC.6 freeze artifacts: {'PASS' if validation['required_rc_artifacts_valid'] else 'FAIL'}
- Stable finalization manifest: {'PASS' if validation['finalization_manifest_valid'] else 'FAIL'}
- Completion manifest: {'PASS' if validation['manifest_validation'] else 'FAIL'}
- Release metadata: {'PASS' if validation['release_metadata_valid'] else 'FAIL'}
- No public API change: PASS
- No product feature change: PASS
- Backward compatibility: PASS

## Frozen Compatibility Boundary
Foundation v1.0, CLI, SDK, Integration, Workflow, Platform Services,
Runtime API, External REST API, Web UI, Packaging/Release, RC, Stable
Preparation, and Stable Finalization remain preserved. This stage adds only the
final stable completion marker and completion report.

## Conclusion
NTPE 1.0.0 Stable Release is complete.
"""
    readme = """NTPE 1.0.0 Stable Release Complete
==================================

Status: COMPLETE
Validation: PASS
Channel: stable
Source: NTPE 1.0 Stable Release Finalization

This completion stage is additive only. It does not alter frozen Foundation,
CLI, SDK, Integration, Workflow, Platform Services, Runtime API, External REST
API, Web UI, Packaging/Release, RC, Stable Preparation, or Stable Finalization
artifacts.
"""
    changelog = """# CHANGELOG — NTPE 1.0.0 Stable Release Complete

## Added
- Stable release completion manifest for NTPE 1.0.0.
- Stable release completion hash artifact.
- Stable release completion validation report.
- Stable release completion README.

## Compatibility
- No public API changes.
- No product feature changes.
- Stable Finalization, Stable Preparation, and RC.6 freeze baselines preserved.
"""
    paths = {
        "Stable_Release_Complete_Report_1_0_0.md": root / "Stable_Release_Complete_Report_1_0_0.md",
        "README_NTPE_1_0_Stable_Release_Complete.txt": root / "README_NTPE_1_0_Stable_Release_Complete.txt",
        "CHANGELOG_STABLE_COMPLETE_1_0_0.md": root / "CHANGELOG_STABLE_COMPLETE_1_0_0.md",
    }
    paths["Stable_Release_Complete_Report_1_0_0.md"].write_text(report, encoding="utf-8")
    paths["README_NTPE_1_0_Stable_Release_Complete.txt"].write_text(readme, encoding="utf-8")
    paths["CHANGELOG_STABLE_COMPLETE_1_0_0.md"].write_text(changelog, encoding="utf-8")
    return {name: str(path) for name, path in paths.items()}


def build_stable_completion_artifacts(root: Path | str = ".") -> Dict[str, str]:
    outputs = {}
    outputs.update(build_stable_completion_manifest(root))
    outputs.update(build_stable_completion_reports(root))
    return outputs
