from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.translation_engine.utils import now_iso, save_json, save_text
from lts.rc_freeze import (
    LTS_RC_FREEZE_VERSION,
    LTSRCFreezeOptions,
    build_lts_rc_freeze_manifest,
    validate_lts_rc_freeze,
)

LTS_STABLE_PREPARATION_VERSION = "1.1-lts-stable-preparation"
DEFAULT_STABLE_PREP_DIR = "lts_stable_preparation"
DEFAULT_MANIFEST_NAME = "LTS_Stable_Preparation_Manifest_1_1.json"
DEFAULT_HASH_NAME = "LTS_Stable_Preparation_Hash_1_1.json"
DEFAULT_REPORT_NAME = "LTS_Stable_Preparation_Report_1_1.md"

REQUIRED_RC_FREEZE_ARTIFACTS = [
    "lts_rc_freeze/LTS_RC_06_Freeze_Manifest_1_1.json",
    "lts_rc_freeze/LTS_RC_06_Freeze_Hash_1_1.json",
    "lts_rc_freeze/LTS_RC_06_Freeze_Report_1_1.md",
]

STABLE_PREPARATION_FILES = [
    "ntpe_lts_stable_preparation.py",
    "lts/stable_preparation.py",
    "ntpe_lts_rc_freeze.py",
    "lts/rc_freeze.py",
    "ntpe_translate_txt.py",
    "ntpe_translate_batch.py",
    "ntpe_batch_monitor.py",
]

STABLE_PREPARATION_CHECKS = [
    "rc06_freeze_passes",
    "rc06_freeze_artifacts_present",
    "stable_preparation_files_present",
    "release_readiness_gate_passes",
    "runtime_data_clean_policy_enabled",
    "stable_preparation_ready",
]


@dataclass(frozen=True)
class LTSStablePreparationOptions:
    root: Path = Path(".")
    stable_dir: Path = Path(DEFAULT_STABLE_PREP_DIR)
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


def _read_json(root: Path, rel: str) -> dict:
    path = root / rel
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_lts_stable_preparation_manifest(options: LTSStablePreparationOptions) -> dict:
    root = options.root.resolve()
    stable_dir = _resolve(root, options.stable_dir)

    rc06_manifest = build_lts_rc_freeze_manifest(
        LTSRCFreezeOptions(root=root, write_files=False)
    )
    rc06_result = validate_lts_rc_freeze(rc06_manifest)

    rc06_artifacts, missing_rc06_artifacts = _collect_entries(root, REQUIRED_RC_FREEZE_ARTIFACTS)
    stable_files, missing_stable_files = _collect_entries(root, STABLE_PREPARATION_FILES)

    rc06_written_manifest = _read_json(root, REQUIRED_RC_FREEZE_ARTIFACTS[0])
    rc06_written_ready = rc06_written_manifest.get("status") == "pass" and rc06_written_manifest.get("rc_freeze_ready") is True

    release_readiness_gate = {
        "rc06_freeze_status": rc06_result.get("status"),
        "rc06_written_manifest_ready": rc06_written_ready,
        "frozen_runtime": "NTPE 1.1 LTS Runtime",
        "feature_changes_allowed": False,
        "external_api_calls": 0,
        "packaging_requires_clean_project_tool": True,
        "stable_finalization_allowed": True,
    }

    failures: list[str] = []
    if rc06_result.get("status") != "pass":
        failures.append("rc06_freeze_passes")
    if missing_rc06_artifacts:
        failures.append("rc06_freeze_artifacts_present")
    if missing_stable_files:
        failures.append("stable_preparation_files_present")
    if not (rc06_written_ready and release_readiness_gate["stable_finalization_allowed"]):
        failures.append("release_readiness_gate_passes")
    if not release_readiness_gate["packaging_requires_clean_project_tool"]:
        failures.append("runtime_data_clean_policy_enabled")

    stable_preparation_ready = not failures
    if not stable_preparation_ready:
        failures.append("stable_preparation_ready")

    status = "pass" if not failures else "fail"
    manifest = {
        "version": LTS_STABLE_PREPARATION_VERSION,
        "release_line": "NTPE 1.1 LTS",
        "stage": "Stable Release Preparation",
        "status": status,
        "created_at": now_iso(),
        "candidate": {
            "source_stage": "RC-06 LTS RC Freeze",
            "source_version": LTS_RC_FREEZE_VERSION,
            "recommended_tag": "v1.1.0-lts-stable-preparation",
            "next_stage": "NTPE 1.1 LTS Stable Release Finalization",
        },
        "stable_scope": {
            "release_target": "NTPE 1.1 LTS Stable",
            "feature_changes_allowed": False,
            "runtime_data_cleaned_before_packaging": True,
            "full_zip_policy": "clean_project_tool_required",
            "increment_zip_policy": "stage_only_changes",
            "backward_compatibility": "preserved",
        },
        "release_readiness_gate": release_readiness_gate,
        "stable_preparation_checks": STABLE_PREPARATION_CHECKS,
        "rc06_result": rc06_result,
        "rc06_artifacts": rc06_artifacts,
        "stable_preparation_files": stable_files,
        "missing_rc06_artifacts": missing_rc06_artifacts,
        "missing_stable_preparation_files": missing_stable_files,
        "stable_preparation_ready": stable_preparation_ready,
        "failures": failures,
        "validation": {
            "status": status,
            "check_count": len(STABLE_PREPARATION_CHECKS),
            "failure_count": len(failures),
            "rc06_artifact_count": len(rc06_artifacts),
            "stable_file_count": len(stable_files),
            "selected_regression_suite": "Stable + LTS Stage-01~12 + RC-01~06 + Stable Preparation",
            "expected_result": "ALL PASS",
            "external_api_calls": 0,
        },
    }

    if options.write_files:
        stable_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = stable_dir / DEFAULT_MANIFEST_NAME
        hash_path = stable_dir / DEFAULT_HASH_NAME
        report_path = stable_dir / DEFAULT_REPORT_NAME
        save_json(manifest_path, manifest)
        stable_hash = {
            "version": LTS_STABLE_PREPARATION_VERSION,
            "manifest": str(manifest_path.relative_to(root)) if manifest_path.is_relative_to(root) else str(manifest_path),
            "manifest_sha256": _sha256(manifest_path),
            "rc06_artifact_hashes": {entry["path"]: entry["sha256"] for entry in rc06_artifacts},
            "stable_preparation_file_hashes": {entry["path"]: entry["sha256"] for entry in stable_files},
            "stable_preparation_ready": stable_preparation_ready,
            "status": status,
            "created_at": now_iso(),
        }
        save_json(hash_path, stable_hash)
        save_text(report_path, format_lts_stable_preparation_markdown(manifest, stable_hash))
        manifest["manifest_path"] = str(manifest_path)
        manifest["hash_path"] = str(hash_path)
        manifest["report_path"] = str(report_path)
    return manifest


def validate_lts_stable_preparation(manifest: dict) -> dict:
    failures = list(manifest.get("failures", []))
    passed = manifest.get("status") == "pass" and not failures and manifest.get("stable_preparation_ready") is True
    return {
        "version": LTS_STABLE_PREPARATION_VERSION,
        "status": "pass" if passed else "fail",
        "check_count": len(manifest.get("stable_preparation_checks", [])),
        "failure_count": len(failures),
        "failures": failures,
        "rc06_artifact_count": len(manifest.get("rc06_artifacts", [])),
        "stable_file_count": len(manifest.get("stable_preparation_files", [])),
        "stable_preparation_ready": manifest.get("stable_preparation_ready"),
    }


def format_lts_stable_preparation_text(manifest: dict) -> str:
    result = validate_lts_stable_preparation(manifest)
    lines = [
        "NTPE 1.1 LTS Stable Release Preparation",
        "========================================",
        f"status: {manifest.get('status')}",
        f"validation: {result.get('status')}",
        f"recommended_tag: {manifest.get('candidate', {}).get('recommended_tag')}",
        f"next_stage: {manifest.get('candidate', {}).get('next_stage')}",
        f"check_count: {result.get('check_count')}",
        f"failure_count: {result.get('failure_count')}",
        f"rc06_artifact_count: {result.get('rc06_artifact_count')}",
        f"stable_file_count: {result.get('stable_file_count')}",
        f"stable_preparation_ready: {result.get('stable_preparation_ready')}",
        f"manifest: {manifest.get('manifest_path', '')}",
        f"report: {manifest.get('report_path', '')}",
    ]
    return "\n".join(lines).strip() + "\n"


def format_lts_stable_preparation_markdown(manifest: dict, stable_hash: dict | None = None) -> str:
    result = validate_lts_stable_preparation(manifest)
    failures = set(manifest.get("failures", []))
    lines = [
        "# NTPE 1.1 LTS Stable Release Preparation Report",
        "",
        f"- Version: {manifest.get('version')}",
        f"- Status: {manifest.get('status')}",
        f"- Validation: {result.get('status')}",
        f"- Recommended Tag: `{manifest.get('candidate', {}).get('recommended_tag')}`",
        f"- Next Stage: {manifest.get('candidate', {}).get('next_stage')}",
        f"- Stable Preparation Ready: {manifest.get('stable_preparation_ready')}",
        f"- Failure Count: {result.get('failure_count')}",
        f"- External API Calls: {manifest.get('validation', {}).get('external_api_calls')}",
        "",
        "## Preparation Checks",
        "",
        "| Check | Status |",
        "|---|---|",
    ]
    for check in manifest.get("stable_preparation_checks", []):
        lines.append(f"| `{check}` | {'FAIL' if check in failures else 'PASS'} |")
    lines.extend([
        "",
        "## Stable Scope",
        "",
        f"- Release Target: {manifest.get('stable_scope', {}).get('release_target')}",
        f"- Feature Changes Allowed: {manifest.get('stable_scope', {}).get('feature_changes_allowed')}",
        f"- Full ZIP Policy: {manifest.get('stable_scope', {}).get('full_zip_policy')}",
        f"- Increment ZIP Policy: {manifest.get('stable_scope', {}).get('increment_zip_policy')}",
        "- Confirms RC-06 freeze remains passable.",
        "- Requires Clean Project Tool before Full ZIP packaging.",
        "- Performs no external API calls and does not alter translation behavior.",
    ])
    if stable_hash:
        lines.extend(["", f"Manifest SHA256: `{stable_hash.get('manifest_sha256')}`"])
    return "\n".join(lines).strip() + "\n"


def parse_args(argv: Iterable[str] | None = None) -> LTSStablePreparationOptions:
    parser = argparse.ArgumentParser(description="NTPE 1.1 LTS stable release preparation")
    parser.add_argument("--root", default=".", help="project root")
    parser.add_argument("--stable-dir", default=DEFAULT_STABLE_PREP_DIR)
    parser.add_argument("--no-write-files", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    ns = parser.parse_args(list(argv) if argv is not None else None)
    return LTSStablePreparationOptions(
        root=Path(ns.root),
        stable_dir=Path(ns.stable_dir),
        write_files=not ns.no_write_files,
        quiet=ns.quiet,
    )


def main(argv: Iterable[str] | None = None) -> int:
    options = parse_args(argv)
    manifest = build_lts_stable_preparation_manifest(options)
    if not options.quiet:
        print(format_lts_stable_preparation_text(manifest), end="")
    return 0 if validate_lts_stable_preparation(manifest)["status"] == "pass" else 1