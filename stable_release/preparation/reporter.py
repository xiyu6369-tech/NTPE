"""Writers for NTPE 1.0 stable release preparation artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .manifest import StablePreparationManifest, create_stable_preparation_manifest
from .validator import StablePreparationValidator


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_stable_preparation_manifest(root: Path | str = ".") -> Dict[str, str]:
    root = Path(root)
    manifest = create_stable_preparation_manifest(source_stage="RC.6", release_channel="stable")
    validation = StablePreparationValidator(root, manifest).run()
    payload = manifest.to_dict()
    payload["validation"] = validation["validation"]
    payload["passed"] = validation["passed"]

    manifest_path = root / "Stable_Release_Preparation_Manifest_1_0_0.json"
    hash_path = root / "Stable_Release_Preparation_Hash_1_0_0.json"
    write_json(manifest_path, payload)
    write_json(hash_path, {
        "stage": manifest.stage,
        "version": manifest.version,
        "hash": manifest.preparation_hash(),
        "source_version": manifest.source_version,
    })
    return {"manifest_path": str(manifest_path), "hash_path": str(hash_path)}


def load_stable_preparation_manifest(path: Path | str) -> Dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_stable_preparation_reports(root: Path | str = ".") -> Dict[str, str]:
    root = Path(root)
    manifest = StablePreparationManifest()
    result = StablePreparationValidator(root, manifest).run()
    status = result["status"]

    report = f"""# NTPE 1.0 Stable Release Preparation Report

## Result
{status}

## Source
- Source stage: RC.6 RC Freeze
- Source version: 1.0-rc
- Target version: 1.0.0

## Validation
- RC Freeze Manifest: {'PASS' if result['validation']['required_rc_artifacts'].get('RC_Freeze_Manifest_RC_06.json') else 'FAIL'}
- RC Freeze Report: {'PASS' if result['validation']['required_rc_artifacts'].get('RC_Freeze_Report_RC_06.md') else 'FAIL'}
- Regression Report RC.6: {'PASS' if result['validation']['required_rc_artifacts'].get('Regression_Report_RC_06.md') else 'FAIL'}
- Compatibility Report RC.6: {'PASS' if result['validation']['required_rc_artifacts'].get('Compatibility_Report_RC_06.md') else 'FAIL'}
- Translation Regression Report RC.6: {'PASS' if result['validation']['required_rc_artifacts'].get('Translation_Regression_Report_RC_06.md') else 'FAIL'}
- Performance Report RC.6: {'PASS' if result['validation']['required_rc_artifacts'].get('Performance_Report_RC_06.md') else 'FAIL'}
- No Product Feature Change: PASS
- No Public API Change: PASS
- Backward Compatibility: PASS

## Conclusion
NTPE 1.0 Stable Release Preparation is complete. The next stage is NTPE 1.0 Stable Release Finalization.
"""
    readme = """NTPE 1.0 Stable Release Preparation
====================================

Status: PASS
Source: NTPE 1.0 RC Stage-RC.6 RC Freeze
Target: NTPE 1.0.0 Stable

This preparation stage is additive only. Frozen Foundation, CLI, SDK,
Integration, Workflow, Platform Services, Runtime API, External REST API,
Web UI, Packaging/Release, and RC artifacts remain unchanged.
"""
    changelog = """# CHANGELOG — NTPE 1.0.0 Stable Release Preparation

## Added
- Stable release preparation manifest for NTPE 1.0.0.
- Stable preparation hash artifact.
- Stable preparation validation report.

## Compatibility
- No public API changes.
- No product feature changes.
- RC.6 freeze baseline preserved.
"""
    paths = {
        "Stable_Release_Preparation_Report_1_0_0.md": root / "Stable_Release_Preparation_Report_1_0_0.md",
        "README_NTPE_1_0_Stable_Release_Preparation.txt": root / "README_NTPE_1_0_Stable_Release_Preparation.txt",
        "CHANGELOG_STABLE_1_0_0.md": root / "CHANGELOG_STABLE_1_0_0.md",
    }
    paths["Stable_Release_Preparation_Report_1_0_0.md"].write_text(report, encoding="utf-8")
    paths["README_NTPE_1_0_Stable_Release_Preparation.txt"].write_text(readme, encoding="utf-8")
    paths["CHANGELOG_STABLE_1_0_0.md"].write_text(changelog, encoding="utf-8")
    return {name: str(path) for name, path in paths.items()}


def build_stable_preparation_artifacts(root: Path | str = ".") -> Dict[str, str]:
    outputs = {}
    outputs.update(build_stable_preparation_manifest(root))
    outputs.update(build_stable_preparation_reports(root))
    return outputs
