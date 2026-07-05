from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.translation_engine.utils import now_iso, save_json, save_text
from lts.release_candidate import (
    DEFAULT_MANIFEST_NAME as LTS_RC_MANIFEST_NAME,
    LTS_RELEASE_CANDIDATE_VERSION,
    build_lts_release_candidate_manifest,
    validate_lts_release_candidate,
    LTSReleaseCandidateOptions,
)
from lts.runtime_freeze import (
    FROZEN_RUNTIME_FILES,
    REQUIRED_STAGE_REPORTS,
    build_runtime_freeze_manifest,
    validate_runtime_freeze,
    RuntimeFreezeOptions,
)

LTS_RC_REGRESSION_VERSION = "1.1-lts-rc-01"
DEFAULT_REGRESSION_DIR = "lts_rc_regression"
DEFAULT_MANIFEST_NAME = "LTS_RC_01_Regression_Validation_Manifest_1_1.json"
DEFAULT_HASH_NAME = "LTS_RC_01_Regression_Validation_Hash_1_1.json"
DEFAULT_REPORT_NAME = "LTS_RC_01_Regression_Validation_Report_1_1.md"

REQUIRED_RC_ARTIFACTS = [
    "lts_release_candidate/LTS_Release_Candidate_Manifest_1_1.json",
    "lts_release_candidate/LTS_Release_Candidate_Hash_1_1.json",
    "lts_release_candidate/LTS_Release_Candidate_Preparation_Report_1_1.md",
    "lts_release_candidate/RELEASE_NOTES_NTPE_1_1_LTS_RC.md",
]

REGRESSION_CHECKS = [
    "stable_release_complete_marker",
    "lts_runtime_freeze_validation",
    "lts_release_candidate_validation",
    "frozen_runtime_files_present",
    "stage_report_chain_present",
    "rc_artifact_chain_present",
]

@dataclass(frozen=True)
class LTSRCRegressionOptions:
    root: Path = Path(".")
    regression_dir: Path = Path(DEFAULT_REGRESSION_DIR)
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


def build_lts_rc_regression_manifest(options: LTSRCRegressionOptions) -> dict:
    root = options.root.resolve()
    regression_dir = _resolve(root, options.regression_dir)

    runtime_manifest = build_runtime_freeze_manifest(RuntimeFreezeOptions(root=root, write_files=False))
    runtime_result = validate_runtime_freeze(runtime_manifest)
    rc_manifest = build_lts_release_candidate_manifest(LTSReleaseCandidateOptions(root=root, write_files=False))
    rc_result = validate_lts_release_candidate(rc_manifest)

    runtime_entries, missing_runtime = _collect_entries(root, FROZEN_RUNTIME_FILES)
    stage_report_entries, missing_stage_reports = _collect_entries(root, REQUIRED_STAGE_REPORTS)
    rc_artifact_entries, missing_rc_artifacts = _collect_entries(root, REQUIRED_RC_ARTIFACTS)

    stable_marker_candidates = [
        "Stable_Release_Complete_Manifest_1_0_0.json",
        "Stable_Release_Complete_Report_1_0_0.md",
        "Stable_Release_Complete_Hash_1_0_0.json",
    ]
    stable_entries, missing_stable = _collect_entries(root, stable_marker_candidates)
    stable_marker = stable_entries[0] if stable_entries else None

    failures = []
    if runtime_result["status"] != "pass":
        failures.append("lts_runtime_freeze_validation")
    if rc_result["status"] != "pass":
        failures.append("lts_release_candidate_validation")
    if missing_runtime:
        failures.append("frozen_runtime_files_present")
    if missing_stage_reports:
        failures.append("stage_report_chain_present")
    if missing_rc_artifacts:
        failures.append("rc_artifact_chain_present")
    if missing_stable:
        failures.append("stable_release_complete_artifacts")

    status = "pass" if not failures else "fail"
    manifest = {
        "version": LTS_RC_REGRESSION_VERSION,
        "release_line": "NTPE 1.1 LTS",
        "stage": "RC-01 Regression Validation",
        "status": status,
        "created_at": now_iso(),
        "candidate": {
            "source_stage": "Stage-12 LTS Release Candidate Preparation",
            "source_version": LTS_RELEASE_CANDIDATE_VERSION,
            "recommended_tag": "v1.1.0-lts-rc-01-regression",
            "base_candidate_manifest": f"lts_release_candidate/{LTS_RC_MANIFEST_NAME}",
        },
        "compatibility_policy": {
            "ntpe_1_0_stable": "preserved",
            "foundation_v1_0": "frozen",
            "cli": "frozen",
            "sdk": "frozen",
            "runtime_api": "frozen",
            "external_rest_api": "frozen",
            "web_ui": "frozen",
            "lts_runtime": "frozen_by_stage_11",
            "rc_01_change_type": "regression_validation_metadata_only",
        },
        "regression_checks": REGRESSION_CHECKS,
        "runtime_validation": runtime_result,
        "release_candidate_validation": rc_result,
        "stable_marker": stable_marker,
        "stable_artifacts": stable_entries,
        "runtime_files": runtime_entries,
        "stage_reports": stage_report_entries,
        "rc_artifacts": rc_artifact_entries,
        "missing_stable_markers": missing_stable,
        "missing_runtime_files": missing_runtime,
        "missing_stage_reports": missing_stage_reports,
        "missing_rc_artifacts": missing_rc_artifacts,
        "failures": failures,
        "validation": {
            "status": status,
            "check_count": len(REGRESSION_CHECKS),
            "failure_count": len(failures),
            "runtime_file_count": len(runtime_entries),
            "stage_report_count": len(stage_report_entries),
            "rc_artifact_count": len(rc_artifact_entries),
            "selected_regression_suite": "Stable + LTS Stage-01~12 + Clean Project Tool + RC-01",
            "expected_result": "ALL PASS",
        },
    }

    if options.write_files:
        regression_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = regression_dir / DEFAULT_MANIFEST_NAME
        hash_path = regression_dir / DEFAULT_HASH_NAME
        report_path = regression_dir / DEFAULT_REPORT_NAME
        save_json(manifest_path, manifest)
        regression_hash = {
            "version": LTS_RC_REGRESSION_VERSION,
            "manifest": str(manifest_path.relative_to(root)) if manifest_path.is_relative_to(root) else str(manifest_path),
            "manifest_sha256": _sha256(manifest_path),
            "runtime_file_hashes": {entry["path"]: entry["sha256"] for entry in runtime_entries},
            "stage_report_hashes": {entry["path"]: entry["sha256"] for entry in stage_report_entries},
            "rc_artifact_hashes": {entry["path"]: entry["sha256"] for entry in rc_artifact_entries},
            "status": status,
            "created_at": now_iso(),
        }
        save_json(hash_path, regression_hash)
        save_text(report_path, format_lts_rc_regression_markdown(manifest, regression_hash))
        manifest["manifest_path"] = str(manifest_path)
        manifest["hash_path"] = str(hash_path)
        manifest["report_path"] = str(report_path)
    return manifest


def validate_lts_rc_regression(manifest: dict) -> dict:
    failures = list(manifest.get("failures", []))
    passed = manifest.get("status") == "pass" and not failures
    return {
        "version": LTS_RC_REGRESSION_VERSION,
        "status": "pass" if passed else "fail",
        "check_count": len(manifest.get("regression_checks", [])),
        "failure_count": len(failures),
        "failures": failures,
        "runtime_file_count": len(manifest.get("runtime_files", [])),
        "stage_report_count": len(manifest.get("stage_reports", [])),
        "rc_artifact_count": len(manifest.get("rc_artifacts", [])),
    }


def format_lts_rc_regression_text(manifest: dict) -> str:
    result = validate_lts_rc_regression(manifest)
    lines = [
        "NTPE 1.1 LTS RC-01 Regression Validation",
        "==========================================",
        f"status: {manifest.get('status')}",
        f"validation: {result.get('status')}",
        f"recommended_tag: {manifest.get('candidate', {}).get('recommended_tag')}",
        f"check_count: {result.get('check_count')}",
        f"failure_count: {result.get('failure_count')}",
        f"runtime_file_count: {result.get('runtime_file_count')}",
        f"stage_report_count: {result.get('stage_report_count')}",
        f"rc_artifact_count: {result.get('rc_artifact_count')}",
        f"manifest: {manifest.get('manifest_path', '')}",
        f"report: {manifest.get('report_path', '')}",
    ]
    return "\n".join(lines).strip() + "\n"


def format_lts_rc_regression_markdown(manifest: dict, regression_hash: dict | None = None) -> str:
    result = validate_lts_rc_regression(manifest)
    lines = [
        "# NTPE 1.1 LTS RC-01 Regression Validation Report",
        "",
        f"- Version: {manifest.get('version')}",
        f"- Status: {manifest.get('status')}",
        f"- Validation: {result.get('status')}",
        f"- Recommended Tag: `{manifest.get('candidate', {}).get('recommended_tag')}`",
        f"- Regression Checks: {result.get('check_count')}",
        f"- Failure Count: {result.get('failure_count')}",
        "",
        "## Regression Gate",
        "",
        "| Check | Status |",
        "|---|---|",
    ]
    failures = set(manifest.get("failures", []))
    for check in manifest.get("regression_checks", []):
        lines.append(f"| `{check}` | {'FAIL' if check in failures else 'PASS'} |")
    lines.extend([
        "",
        "## Validation Scope",
        "",
        "- Confirms NTPE 1.0 Stable completion artifacts are present.",
        "- Revalidates Stage-11 frozen LTS runtime inputs.",
        "- Revalidates Stage-12 release-candidate artifacts.",
        "- Records runtime, stage report, and RC artifact hashes for repeatable RC validation.",
        "- Does not modify Foundation v1.0, CLI, SDK, Runtime API, REST API, Web UI, or frozen LTS runtime behavior.",
        "",
        "## Compatibility Policy",
        "",
    ])
    for key, value in manifest.get("compatibility_policy", {}).items():
        lines.append(f"- {key}: {value}")
    if regression_hash:
        lines.extend(["", f"Manifest SHA256: `{regression_hash.get('manifest_sha256')}`"])
    return "\n".join(lines).strip() + "\n"


def parse_args(argv: Iterable[str] | None = None) -> LTSRCRegressionOptions:
    parser = argparse.ArgumentParser(description="NTPE 1.1 LTS RC-01 regression validation")
    parser.add_argument("--root", default=".", help="project root")
    parser.add_argument("--regression-dir", default=DEFAULT_REGRESSION_DIR)
    parser.add_argument("--no-write-files", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    ns = parser.parse_args(list(argv) if argv is not None else None)
    return LTSRCRegressionOptions(
        root=Path(ns.root),
        regression_dir=Path(ns.regression_dir),
        write_files=not ns.no_write_files,
        quiet=ns.quiet,
    )


def main(argv: Iterable[str] | None = None) -> int:
    options = parse_args(argv)
    manifest = build_lts_rc_regression_manifest(options)
    if not options.quiet:
        print(format_lts_rc_regression_text(manifest), end="")
    return 0 if validate_lts_rc_regression(manifest)["status"] == "pass" else 1
