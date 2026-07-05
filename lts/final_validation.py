from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.translation_engine.utils import now_iso, save_json, save_text
from lts.regression_validation import (
    LTS_RC_REGRESSION_VERSION,
    LTSRCRegressionOptions,
    build_lts_rc_regression_manifest,
    validate_lts_rc_regression,
)
from lts.compatibility_validation import (
    LTS_RC_COMPATIBILITY_VERSION,
    LTSRCCompatibilityOptions,
    build_lts_rc_compatibility_manifest,
    validate_lts_rc_compatibility,
)
from lts.performance_validation import (
    LTS_RC_PERFORMANCE_VERSION,
    LTSRCPerformanceOptions,
    build_lts_rc_performance_manifest,
    validate_lts_rc_performance,
)
from lts.quality_validation import (
    LTS_RC_QUALITY_VERSION,
    LTSRCQualityOptions,
    build_lts_rc_quality_manifest,
    validate_lts_rc_quality,
)

LTS_RC_FINAL_VERSION = "1.1-lts-rc-05"
DEFAULT_FINAL_DIR = "lts_rc_final_validation"
DEFAULT_MANIFEST_NAME = "LTS_RC_05_Final_Validation_Manifest_1_1.json"
DEFAULT_HASH_NAME = "LTS_RC_05_Final_Validation_Hash_1_1.json"
DEFAULT_REPORT_NAME = "LTS_RC_05_Final_Validation_Report_1_1.md"

REQUIRED_RC_ARTIFACTS = [
    "lts_rc_regression/LTS_RC_01_Regression_Validation_Manifest_1_1.json",
    "lts_rc_regression/LTS_RC_01_Regression_Validation_Hash_1_1.json",
    "lts_rc_regression/LTS_RC_01_Regression_Validation_Report_1_1.md",
    "lts_rc_compatibility/LTS_RC_02_Compatibility_Validation_Manifest_1_1.json",
    "lts_rc_compatibility/LTS_RC_02_Compatibility_Validation_Hash_1_1.json",
    "lts_rc_compatibility/LTS_RC_02_Compatibility_Validation_Report_1_1.md",
    "lts_rc_performance/LTS_RC_03_Performance_Long_Run_Validation_Manifest_1_1.json",
    "lts_rc_performance/LTS_RC_03_Performance_Long_Run_Validation_Hash_1_1.json",
    "lts_rc_performance/LTS_RC_03_Performance_Long_Run_Validation_Report_1_1.md",
    "lts_rc_quality/LTS_RC_04_Translation_Quality_QA_Validation_Manifest_1_1.json",
    "lts_rc_quality/LTS_RC_04_Translation_Quality_QA_Validation_Hash_1_1.json",
    "lts_rc_quality/LTS_RC_04_Translation_Quality_QA_Validation_Report_1_1.md",
]

FINAL_VALIDATION_FILES = [
    "ntpe_lts_rc_regression.py",
    "ntpe_lts_rc_compatibility.py",
    "ntpe_lts_rc_performance.py",
    "ntpe_lts_rc_quality.py",
    "ntpe_lts_rc_final_validation.py",
    "lts/regression_validation.py",
    "lts/compatibility_validation.py",
    "lts/performance_validation.py",
    "lts/quality_validation.py",
    "lts/final_validation.py",
]

FINAL_CHECKS = [
    "rc01_regression_validation_passes",
    "rc02_compatibility_validation_passes",
    "rc03_performance_validation_passes",
    "rc04_quality_validation_passes",
    "rc_artifact_chain_present",
    "final_validation_files_present",
    "frozen_compatibility_policy_preserved",
    "release_candidate_gate_ready",
]


@dataclass(frozen=True)
class LTSRCFinalValidationOptions:
    root: Path = Path(".")
    final_dir: Path = Path(DEFAULT_FINAL_DIR)
    write_files: bool = True
    quiet: bool = False


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve(root: Path, path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else root / p


def _file_entry(root: Path, rel: str) -> dict | None:
    path = root / rel
    if not path.exists() or not path.is_file():
        return None
    return {"path": rel, "sha256": _sha256(path), "size_bytes": path.stat().st_size}


def _collect_entries(root: Path, rels: Iterable[str]) -> tuple[list[dict], list[str]]:
    entries: list[dict] = []
    missing: list[str] = []
    for rel in rels:
        entry = _file_entry(root, rel)
        if entry:
            entries.append(entry)
        else:
            missing.append(rel)
    return entries, missing


def _gate_status(name: str, result: dict) -> dict:
    return {
        "name": name,
        "status": result.get("status"),
        "failure_count": result.get("failure_count", 0),
        "check_count": result.get("check_count", 0),
        "version": result.get("version"),
    }


def build_lts_rc_final_validation_manifest(options: LTSRCFinalValidationOptions) -> dict:
    root = options.root.resolve()
    final_dir = _resolve(root, options.final_dir)

    regression_manifest = build_lts_rc_regression_manifest(LTSRCRegressionOptions(root=root, write_files=False))
    compatibility_manifest = build_lts_rc_compatibility_manifest(LTSRCCompatibilityOptions(root=root, write_files=False))
    performance_manifest = build_lts_rc_performance_manifest(LTSRCPerformanceOptions(root=root, write_files=False))
    quality_manifest = build_lts_rc_quality_manifest(LTSRCQualityOptions(root=root, write_files=False))

    regression_result = validate_lts_rc_regression(regression_manifest)
    compatibility_result = validate_lts_rc_compatibility(compatibility_manifest)
    performance_result = validate_lts_rc_performance(performance_manifest)
    quality_result = validate_lts_rc_quality(quality_manifest)

    rc_artifacts, missing_rc_artifacts = _collect_entries(root, REQUIRED_RC_ARTIFACTS)
    final_files, missing_final_files = _collect_entries(root, FINAL_VALIDATION_FILES)

    compatibility_policy = quality_manifest.get("compatibility_policy", {})
    frozen_policy_preserved = all(
        compatibility_policy.get(key) == expected for key, expected in {
            "ntpe_1_0_stable": "preserved",
            "foundation_v1_0": "frozen",
            "cli": "frozen",
            "sdk": "frozen",
            "runtime_api": "frozen",
            "external_rest_api": "frozen",
            "web_ui": "frozen",
            "lts_runtime": "frozen_by_stage_11",
        }.items()
    )

    gate_results = {
        "rc01_regression": _gate_status("RC-01 Regression Validation", regression_result),
        "rc02_compatibility": _gate_status("RC-02 Compatibility Validation", compatibility_result),
        "rc03_performance": _gate_status("RC-03 Performance / Long-Run Validation", performance_result),
        "rc04_quality": _gate_status("RC-04 Translation Quality / QA Validation", quality_result),
    }

    failures: list[str] = []
    if regression_result.get("status") != "pass":
        failures.append("rc01_regression_validation_passes")
    if compatibility_result.get("status") != "pass":
        failures.append("rc02_compatibility_validation_passes")
    if performance_result.get("status") != "pass":
        failures.append("rc03_performance_validation_passes")
    if quality_result.get("status") != "pass":
        failures.append("rc04_quality_validation_passes")
    if missing_rc_artifacts:
        failures.append("rc_artifact_chain_present")
    if missing_final_files:
        failures.append("final_validation_files_present")
    if not frozen_policy_preserved:
        failures.append("frozen_compatibility_policy_preserved")

    release_candidate_gate_ready = not failures
    if not release_candidate_gate_ready:
        failures.append("release_candidate_gate_ready")

    status = "pass" if not failures else "fail"
    manifest = {
        "version": LTS_RC_FINAL_VERSION,
        "release_line": "NTPE 1.1 LTS",
        "stage": "RC-05 Release Candidate Final Validation",
        "status": status,
        "created_at": now_iso(),
        "candidate": {
            "source_stage": "RC-04 Translation Quality / QA Validation",
            "source_version": LTS_RC_QUALITY_VERSION,
            "recommended_tag": "v1.1.0-lts-rc-05-final-validation",
            "next_stage": "NTPE 1.1 LTS RC Freeze",
        },
        "rc_versions": {
            "rc01_regression": LTS_RC_REGRESSION_VERSION,
            "rc02_compatibility": LTS_RC_COMPATIBILITY_VERSION,
            "rc03_performance": LTS_RC_PERFORMANCE_VERSION,
            "rc04_quality": LTS_RC_QUALITY_VERSION,
            "rc05_final": LTS_RC_FINAL_VERSION,
        },
        "final_checks": FINAL_CHECKS,
        "gate_results": gate_results,
        "rc_artifacts": rc_artifacts,
        "final_validation_files": final_files,
        "missing_rc_artifacts": missing_rc_artifacts,
        "missing_final_validation_files": missing_final_files,
        "compatibility_policy": compatibility_policy,
        "frozen_policy_preserved": frozen_policy_preserved,
        "release_candidate_gate_ready": release_candidate_gate_ready,
        "failures": failures,
        "validation": {
            "status": status,
            "check_count": len(FINAL_CHECKS),
            "failure_count": len(failures),
            "rc_artifact_count": len(rc_artifacts),
            "final_file_count": len(final_files),
            "selected_regression_suite": "Stable + LTS Stage-01~12 + RC-01~05",
            "expected_result": "ALL PASS",
            "external_api_calls": 0,
        },
    }

    if options.write_files:
        final_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = final_dir / DEFAULT_MANIFEST_NAME
        hash_path = final_dir / DEFAULT_HASH_NAME
        report_path = final_dir / DEFAULT_REPORT_NAME
        save_json(manifest_path, manifest)
        final_hash = {
            "version": LTS_RC_FINAL_VERSION,
            "manifest": str(manifest_path.relative_to(root)) if manifest_path.is_relative_to(root) else str(manifest_path),
            "manifest_sha256": _sha256(manifest_path),
            "rc_artifact_hashes": {entry["path"]: entry["sha256"] for entry in rc_artifacts},
            "final_validation_file_hashes": {entry["path"]: entry["sha256"] for entry in final_files},
            "release_candidate_gate_ready": release_candidate_gate_ready,
            "status": status,
            "created_at": now_iso(),
        }
        save_json(hash_path, final_hash)
        save_text(report_path, format_lts_rc_final_validation_markdown(manifest, final_hash))
        manifest["manifest_path"] = str(manifest_path)
        manifest["hash_path"] = str(hash_path)
        manifest["report_path"] = str(report_path)
    return manifest


def validate_lts_rc_final_validation(manifest: dict) -> dict:
    failures = list(manifest.get("failures", []))
    passed = manifest.get("status") == "pass" and not failures and manifest.get("release_candidate_gate_ready") is True
    return {
        "version": LTS_RC_FINAL_VERSION,
        "status": "pass" if passed else "fail",
        "check_count": len(manifest.get("final_checks", [])),
        "failure_count": len(failures),
        "failures": failures,
        "rc_artifact_count": len(manifest.get("rc_artifacts", [])),
        "final_file_count": len(manifest.get("final_validation_files", [])),
        "release_candidate_gate_ready": manifest.get("release_candidate_gate_ready"),
    }


def format_lts_rc_final_validation_text(manifest: dict) -> str:
    result = validate_lts_rc_final_validation(manifest)
    lines = [
        "NTPE 1.1 LTS RC-05 Release Candidate Final Validation",
        "========================================================",
        f"status: {manifest.get('status')}",
        f"validation: {result.get('status')}",
        f"recommended_tag: {manifest.get('candidate', {}).get('recommended_tag')}",
        f"next_stage: {manifest.get('candidate', {}).get('next_stage')}",
        f"check_count: {result.get('check_count')}",
        f"failure_count: {result.get('failure_count')}",
        f"rc_artifact_count: {result.get('rc_artifact_count')}",
        f"final_file_count: {result.get('final_file_count')}",
        f"release_candidate_gate_ready: {result.get('release_candidate_gate_ready')}",
        f"manifest: {manifest.get('manifest_path', '')}",
        f"report: {manifest.get('report_path', '')}",
    ]
    return "\n".join(lines).strip() + "\n"


def format_lts_rc_final_validation_markdown(manifest: dict, final_hash: dict | None = None) -> str:
    result = validate_lts_rc_final_validation(manifest)
    failures = set(manifest.get("failures", []))
    lines = [
        "# NTPE 1.1 LTS RC-05 Release Candidate Final Validation Report",
        "",
        f"- Version: {manifest.get('version')}",
        f"- Status: {manifest.get('status')}",
        f"- Validation: {result.get('status')}",
        f"- Recommended Tag: `{manifest.get('candidate', {}).get('recommended_tag')}`",
        f"- Next Stage: {manifest.get('candidate', {}).get('next_stage')}",
        f"- Release Candidate Gate Ready: {manifest.get('release_candidate_gate_ready')}",
        f"- Failure Count: {result.get('failure_count')}",
        f"- External API Calls: {manifest.get('validation', {}).get('external_api_calls')}",
        "",
        "## Final Gate Checks",
        "",
        "| Check | Status |",
        "|---|---|",
    ]
    for check in manifest.get("final_checks", []):
        lines.append(f"| `{check}` | {'FAIL' if check in failures else 'PASS'} |")
    lines.extend([
        "",
        "## RC Gate Summary",
        "",
        "| Gate | Status | Failures |",
        "|---|---:|---:|",
    ])
    for gate in manifest.get("gate_results", {}).values():
        lines.append(f"| {gate.get('name')} | {gate.get('status')} | {gate.get('failure_count')} |")
    lines.extend([
        "",
        "## Validation Scope",
        "",
        "- Confirms RC-01 regression validation remains passable.",
        "- Confirms RC-02 compatibility validation remains passable.",
        "- Confirms RC-03 performance / long-run validation remains passable.",
        "- Confirms RC-04 translation quality / QA validation remains passable.",
        "- Performs no external API calls and does not modify frozen NTPE 1.0 or LTS runtime behavior.",
    ])
    if final_hash:
        lines.extend(["", f"Manifest SHA256: `{final_hash.get('manifest_sha256')}`"])
    return "\n".join(lines).strip() + "\n"


def parse_args(argv: Iterable[str] | None = None) -> LTSRCFinalValidationOptions:
    parser = argparse.ArgumentParser(description="NTPE 1.1 LTS RC-05 final release candidate validation")
    parser.add_argument("--root", default=".", help="project root")
    parser.add_argument("--final-dir", default=DEFAULT_FINAL_DIR)
    parser.add_argument("--no-write-files", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    ns = parser.parse_args(list(argv) if argv is not None else None)
    return LTSRCFinalValidationOptions(
        root=Path(ns.root),
        final_dir=Path(ns.final_dir),
        write_files=not ns.no_write_files,
        quiet=ns.quiet,
    )


def main(argv: Iterable[str] | None = None) -> int:
    options = parse_args(argv)
    manifest = build_lts_rc_final_validation_manifest(options)
    if not options.quiet:
        print(format_lts_rc_final_validation_text(manifest), end="")
    return 0 if validate_lts_rc_final_validation(manifest)["status"] == "pass" else 1
