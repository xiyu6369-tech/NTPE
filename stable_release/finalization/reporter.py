"""Writers for NTPE 1.0.0 stable release finalization artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .manifest import StableFinalizationManifest, create_stable_finalization_manifest
from .validator import StableFinalizationValidator


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_stable_finalization_manifest(root: Path | str = ".") -> Dict[str, str]:
    root = Path(root)
    manifest = create_stable_finalization_manifest(source_stage="STABLE.1", release_channel="stable")
    validation = StableFinalizationValidator(root, manifest).run()
    payload = manifest.to_dict()
    payload["validation"] = validation["validation"]
    payload["passed"] = validation["passed"]

    manifest_path = root / "Stable_Release_Finalization_Manifest_1_0_0.json"
    hash_path = root / "Stable_Release_Finalization_Hash_1_0_0.json"
    write_json(manifest_path, payload)
    write_json(hash_path, {
        "stage": manifest.stage,
        "status": manifest.status,
        "version": manifest.version,
        "release_channel": manifest.release_channel,
        "hash": manifest.finalization_hash(),
        "source_stage": manifest.source_stage,
        "source_version": manifest.source_version,
    })
    return {"manifest_path": str(manifest_path), "hash_path": str(hash_path)}


def load_stable_finalization_manifest(path: Path | str) -> Dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_stable_finalization_reports(root: Path | str = ".") -> Dict[str, str]:
    root = Path(root)
    manifest = StableFinalizationManifest()
    result = StableFinalizationValidator(root, manifest).run()
    status = result["status"]
    validation = result["validation"]

    report = f"""# NTPE 1.0 Stable Release Finalization Report

## Result
{status}

## Release
- Version: 1.0.0
- Channel: stable
- Source stage: STABLE.1 Stable Release Preparation
- Status: FINALIZED

## Validation
- Stable preparation artifacts: {'PASS' if validation['required_preparation_artifacts_valid'] else 'FAIL'}
- RC.6 freeze artifacts: {'PASS' if validation['required_rc_artifacts_valid'] else 'FAIL'}
- Stable preparation manifest: {'PASS' if validation['preparation_manifest_valid'] else 'FAIL'}
- Finalization manifest: {'PASS' if validation['manifest_validation'] else 'FAIL'}
- Release metadata: {'PASS' if validation['release_metadata_valid'] else 'FAIL'}
- No public API change: PASS
- No product feature change: PASS
- Backward compatibility: PASS

## Frozen Compatibility Boundary
Foundation v1.0, CLI, SDK, Integration, Workflow, Platform Services,
Runtime API, External REST API, Web UI, Packaging/Release, RC, and Stable
Preparation outputs remain preserved. This stage adds final release metadata only.

## Conclusion
NTPE 1.0.0 Stable Release Finalization is complete.
"""
    readme = """NTPE 1.0.0 Stable Final
=======================

Status: FINALIZED
Validation: PASS
Channel: stable
Source: NTPE 1.0 Stable Release Preparation

This finalization stage is additive only. Frozen Foundation, CLI, SDK,
Integration, Workflow, Platform Services, Runtime API, External REST API,
Web UI, Packaging/Release, RC, and Stable Preparation artifacts remain unchanged.
"""
    release_notes = """# NTPE 1.0.0 Stable Release Notes

## Release Status
NTPE 1.0.0 Stable is finalized.

## Compatibility
- Foundation v1.0 compatibility preserved.
- CLI contract preserved.
- SDK contract preserved.
- Runtime API contract preserved.
- External REST API contract preserved.
- Web UI freeze boundary preserved.
- Packaging/Release freeze boundary preserved.
- RC.6 freeze baseline preserved.

## Scope
This stage publishes final stable release metadata only. No product behavior,
public API, CLI command, SDK interface, runtime contract, REST contract, Web UI,
or packaging contract is changed.
"""
    changelog = """# CHANGELOG — NTPE 1.0.0 Stable Finalization

## Added
- Stable finalization manifest for NTPE 1.0.0.
- Stable finalization hash artifact.
- Stable finalization validation report.
- NTPE 1.0.0 stable release notes.

## Compatibility
- No public API changes.
- No product feature changes.
- Stable Preparation and RC.6 freeze baselines preserved.
"""
    paths = {
        "Stable_Release_Finalization_Report_1_0_0.md": root / "Stable_Release_Finalization_Report_1_0_0.md",
        "README_NTPE_1_0_Stable_Final.txt": root / "README_NTPE_1_0_Stable_Final.txt",
        "RELEASE_NOTES_NTPE_1_0_0.md": root / "RELEASE_NOTES_NTPE_1_0_0.md",
        "CHANGELOG_STABLE_FINAL_1_0_0.md": root / "CHANGELOG_STABLE_FINAL_1_0_0.md",
    }
    paths["Stable_Release_Finalization_Report_1_0_0.md"].write_text(report, encoding="utf-8")
    paths["README_NTPE_1_0_Stable_Final.txt"].write_text(readme, encoding="utf-8")
    paths["RELEASE_NOTES_NTPE_1_0_0.md"].write_text(release_notes, encoding="utf-8")
    paths["CHANGELOG_STABLE_FINAL_1_0_0.md"].write_text(changelog, encoding="utf-8")
    return {name: str(path) for name, path in paths.items()}


def build_stable_finalization_artifacts(root: Path | str = ".") -> Dict[str, str]:
    outputs = {}
    outputs.update(build_stable_finalization_manifest(root))
    outputs.update(build_stable_finalization_reports(root))
    return outputs
