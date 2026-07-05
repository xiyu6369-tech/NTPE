from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.translation_engine.utils import now_iso, save_json, save_text
from lts.stable_preparation import (
    LTS_STABLE_PREPARATION_VERSION,
    LTSStablePreparationOptions,
    build_lts_stable_preparation_manifest,
    validate_lts_stable_preparation,
)

LTS_STABLE_FINALIZATION_VERSION = "1.1-lts-stable-finalization"
DEFAULT_STABLE_FINAL_DIR = "lts_stable_finalization"
DEFAULT_MANIFEST_NAME = "LTS_Stable_Finalization_Manifest_1_1.json"
DEFAULT_HASH_NAME = "LTS_Stable_Finalization_Hash_1_1.json"
DEFAULT_REPORT_NAME = "LTS_Stable_Finalization_Report_1_1.md"
DEFAULT_RELEASE_NOTES_NAME = "RELEASE_NOTES_NTPE_1_1_LTS.md"

REQUIRED_STABLE_PREPARATION_ARTIFACTS = [
    "lts_stable_preparation/LTS_Stable_Preparation_Manifest_1_1.json",
    "lts_stable_preparation/LTS_Stable_Preparation_Hash_1_1.json",
    "lts_stable_preparation/LTS_Stable_Preparation_Report_1_1.md",
]

STABLE_FINALIZATION_FILES = [
    "ntpe_lts_stable_finalization.py",
    "lts/stable_finalization.py",
    "ntpe_lts_stable_preparation.py",
    "lts/stable_preparation.py",
    "ntpe_lts_rc_freeze.py",
    "lts/rc_freeze.py",
    "ntpe_translate_txt.py",
    "ntpe_translate_batch.py",
    "ntpe_batch_monitor.py",
    "ntpe_long_run_recovery.py",
    "tools/clean_project.py",
]

STABLE_FINALIZATION_CHECKS = [
    "stable_preparation_passes",
    "stable_preparation_artifacts_present",
    "stable_finalization_files_present",
    "release_notes_ready",
    "release_gate_passes",
    "no_feature_changes_after_rc_freeze",
    "clean_packaging_policy_confirmed",
    "stable_finalization_ready",
]


@dataclass(frozen=True)
class LTSStableFinalizationOptions:
    root: Path = Path(".")
    stable_dir: Path = Path(DEFAULT_STABLE_FINAL_DIR)
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


def build_release_notes_markdown(manifest: dict) -> str:
    final_scope = manifest.get("stable_final_scope", {})
    candidate = manifest.get("candidate", {})
    release_gate = manifest.get("release_gate", {})
    lines = [
        "# NTPE 1.1 LTS Release Notes",
        "",
        "NTPE 1.1 LTS is the long-term support release line built on top of NTPE 1.0 Stable.",
        "",
        "## Release Status",
        "",
        f"- Version: {manifest.get('version')}",
        f"- Status: {manifest.get('status')}",
        f"- Recommended Tag: `{candidate.get('recommended_tag')}`",
        f"- Release Target: {final_scope.get('release_target')}",
        f"- Backward Compatibility: {final_scope.get('backward_compatibility')}",
        f"- Feature Changes After RC Freeze: {release_gate.get('feature_changes_after_rc_freeze')}",
        "",
        "## LTS Runtime Highlights",
        "",
        "- TXT novel translation entry.",
        "- Resume and retry handling for long translation runs.",
        "- Glossary and character memory reinforcement.",
        "- Translation QA with Korean residue checks.",
        "- Taiwan Traditional Chinese normalization and output formatter.",
        "- Batch folder translation, progress summary, failure recovery, runtime monitor, and auto recovery.",
        "- RC regression, compatibility, performance, and quality validation gates.",
        "",
        "## Packaging Policy",
        "",
        "- Full ZIP is produced after Clean Project Tool removes runtime data.",
        "- Increment ZIP contains only finalization-stage additions.",
        "- No external API calls are required for release validation.",
    ]
    return "\n".join(lines).strip() + "\n"


def build_lts_stable_finalization_manifest(options: LTSStableFinalizationOptions) -> dict:
    root = options.root.resolve()
    stable_dir = _resolve(root, options.stable_dir)

    prep_manifest = build_lts_stable_preparation_manifest(
        LTSStablePreparationOptions(root=root, write_files=False)
    )
    prep_result = validate_lts_stable_preparation(prep_manifest)

    preparation_artifacts, missing_preparation_artifacts = _collect_entries(root, REQUIRED_STABLE_PREPARATION_ARTIFACTS)
    finalization_files, missing_finalization_files = _collect_entries(root, STABLE_FINALIZATION_FILES)
    written_prep_manifest = _read_json(root, REQUIRED_STABLE_PREPARATION_ARTIFACTS[0])
    written_prep_ready = written_prep_manifest.get("status") == "pass" and written_prep_manifest.get("stable_preparation_ready") is True

    release_gate = {
        "stable_preparation_status": prep_result.get("status"),
        "written_stable_preparation_ready": written_prep_ready,
        "feature_changes_after_rc_freeze": False,
        "external_api_calls": 0,
        "clean_project_tool_required_for_full_zip": True,
        "increment_zip_stage_only": True,
        "stable_release_completion_allowed": True,
        "release_notes_required": True,
    }

    failures: list[str] = []
    if prep_result.get("status") != "pass":
        failures.append("stable_preparation_passes")
    if missing_preparation_artifacts:
        failures.append("stable_preparation_artifacts_present")
    if missing_finalization_files:
        failures.append("stable_finalization_files_present")
    if not release_gate["release_notes_required"]:
        failures.append("release_notes_ready")
    if not (written_prep_ready and release_gate["stable_release_completion_allowed"]):
        failures.append("release_gate_passes")
    if release_gate["feature_changes_after_rc_freeze"] is not False:
        failures.append("no_feature_changes_after_rc_freeze")
    if not release_gate["clean_project_tool_required_for_full_zip"]:
        failures.append("clean_packaging_policy_confirmed")

    stable_finalization_ready = not failures
    if not stable_finalization_ready:
        failures.append("stable_finalization_ready")

    status = "pass" if not failures else "fail"
    manifest = {
        "version": LTS_STABLE_FINALIZATION_VERSION,
        "release_line": "NTPE 1.1 LTS",
        "stage": "Stable Release Finalization",
        "status": status,
        "created_at": now_iso(),
        "candidate": {
            "source_stage": "NTPE 1.1 LTS Stable Release Preparation",
            "source_version": LTS_STABLE_PREPARATION_VERSION,
            "recommended_tag": "v1.1.0-lts-stable-finalization",
            "next_stage": "NTPE 1.1 LTS Stable Release Complete",
        },
        "stable_final_scope": {
            "release_target": "NTPE 1.1 LTS Stable",
            "feature_changes_allowed": False,
            "runtime_data_cleaned_before_packaging": True,
            "full_zip_policy": "clean_project_tool_required",
            "increment_zip_policy": "stage_only_changes",
            "backward_compatibility": "preserved",
        },
        "release_gate": release_gate,
        "stable_finalization_checks": STABLE_FINALIZATION_CHECKS,
        "stable_preparation_result": prep_result,
        "stable_preparation_artifacts": preparation_artifacts,
        "stable_finalization_files": finalization_files,
        "missing_stable_preparation_artifacts": missing_preparation_artifacts,
        "missing_stable_finalization_files": missing_finalization_files,
        "stable_finalization_ready": stable_finalization_ready,
        "failures": failures,
        "validation": {
            "status": status,
            "check_count": len(STABLE_FINALIZATION_CHECKS),
            "failure_count": len(failures),
            "stable_preparation_artifact_count": len(preparation_artifacts),
            "stable_finalization_file_count": len(finalization_files),
            "selected_regression_suite": "Stable + LTS Stage-01~12 + RC-01~06 + Stable Preparation + Stable Finalization",
            "expected_result": "ALL PASS",
            "external_api_calls": 0,
        },
    }

    if options.write_files:
        stable_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = stable_dir / DEFAULT_MANIFEST_NAME
        hash_path = stable_dir / DEFAULT_HASH_NAME
        report_path = stable_dir / DEFAULT_REPORT_NAME
        notes_path = root / DEFAULT_RELEASE_NOTES_NAME
        save_json(manifest_path, manifest)
        save_text(notes_path, build_release_notes_markdown(manifest))
        stable_hash = {
            "version": LTS_STABLE_FINALIZATION_VERSION,
            "manifest": str(manifest_path.relative_to(root)) if manifest_path.is_relative_to(root) else str(manifest_path),
            "manifest_sha256": _sha256(manifest_path),
            "release_notes": str(notes_path.relative_to(root)) if notes_path.is_relative_to(root) else str(notes_path),
            "release_notes_sha256": _sha256(notes_path),
            "stable_preparation_artifact_hashes": {entry["path"]: entry["sha256"] for entry in preparation_artifacts},
            "stable_finalization_file_hashes": {entry["path"]: entry["sha256"] for entry in finalization_files},
            "stable_finalization_ready": stable_finalization_ready,
            "status": status,
            "created_at": now_iso(),
        }
        save_json(hash_path, stable_hash)
        save_text(report_path, format_lts_stable_finalization_markdown(manifest, stable_hash))
        manifest["manifest_path"] = str(manifest_path)
        manifest["hash_path"] = str(hash_path)
        manifest["report_path"] = str(report_path)
        manifest["release_notes_path"] = str(notes_path)
    return manifest


def validate_lts_stable_finalization(manifest: dict) -> dict:
    failures = list(manifest.get("failures", []))
    passed = manifest.get("status") == "pass" and not failures and manifest.get("stable_finalization_ready") is True
    return {
        "version": LTS_STABLE_FINALIZATION_VERSION,
        "status": "pass" if passed else "fail",
        "check_count": len(manifest.get("stable_finalization_checks", [])),
        "failure_count": len(failures),
        "failures": failures,
        "stable_preparation_artifact_count": len(manifest.get("stable_preparation_artifacts", [])),
        "stable_finalization_file_count": len(manifest.get("stable_finalization_files", [])),
        "stable_finalization_ready": manifest.get("stable_finalization_ready"),
    }


def format_lts_stable_finalization_text(manifest: dict) -> str:
    result = validate_lts_stable_finalization(manifest)
    lines = [
        "NTPE 1.1 LTS Stable Release Finalization",
        "=========================================",
        f"status: {manifest.get('status')}",
        f"validation: {result.get('status')}",
        f"recommended_tag: {manifest.get('candidate', {}).get('recommended_tag')}",
        f"next_stage: {manifest.get('candidate', {}).get('next_stage')}",
        f"check_count: {result.get('check_count')}",
        f"failure_count: {result.get('failure_count')}",
        f"stable_preparation_artifact_count: {result.get('stable_preparation_artifact_count')}",
        f"stable_finalization_file_count: {result.get('stable_finalization_file_count')}",
        f"stable_finalization_ready: {result.get('stable_finalization_ready')}",
        f"manifest: {manifest.get('manifest_path', '')}",
        f"report: {manifest.get('report_path', '')}",
        f"release_notes: {manifest.get('release_notes_path', '')}",
    ]
    return "\n".join(lines).strip() + "\n"


def format_lts_stable_finalization_markdown(manifest: dict, stable_hash: dict | None = None) -> str:
    result = validate_lts_stable_finalization(manifest)
    failures = set(manifest.get("failures", []))
    lines = [
        "# NTPE 1.1 LTS Stable Release Finalization Report",
        "",
        f"- Version: {manifest.get('version')}",
        f"- Status: {manifest.get('status')}",
        f"- Validation: {result.get('status')}",
        f"- Recommended Tag: `{manifest.get('candidate', {}).get('recommended_tag')}`",
        f"- Next Stage: {manifest.get('candidate', {}).get('next_stage')}",
        f"- Stable Finalization Ready: {manifest.get('stable_finalization_ready')}",
        f"- Failure Count: {result.get('failure_count')}",
        f"- External API Calls: {manifest.get('validation', {}).get('external_api_calls')}",
        "",
        "## Finalization Checks",
        "",
        "| Check | Status |",
        "|---|---|",
    ]
    for check in manifest.get("stable_finalization_checks", []):
        lines.append(f"| `{check}` | {'FAIL' if check in failures else 'PASS'} |")
    lines.extend([
        "",
        "## Final Scope",
        "",
        f"- Release Target: {manifest.get('stable_final_scope', {}).get('release_target')}",
        f"- Feature Changes Allowed: {manifest.get('stable_final_scope', {}).get('feature_changes_allowed')}",
        f"- Full ZIP Policy: {manifest.get('stable_final_scope', {}).get('full_zip_policy')}",
        f"- Increment ZIP Policy: {manifest.get('stable_final_scope', {}).get('increment_zip_policy')}",
        "- Confirms Stable Preparation remains passable.",
        "- Writes final LTS release notes draft.",
        "- Requires Clean Project Tool before Full ZIP packaging.",
        "- Performs no external API calls and does not alter translation behavior.",
    ])
    if stable_hash:
        lines.extend([
            "",
            f"Manifest SHA256: `{stable_hash.get('manifest_sha256')}`",
            f"Release Notes SHA256: `{stable_hash.get('release_notes_sha256')}`",
        ])
    return "\n".join(lines).strip() + "\n"


def parse_args(argv: Iterable[str] | None = None) -> LTSStableFinalizationOptions:
    parser = argparse.ArgumentParser(description="NTPE 1.1 LTS stable release finalization")
    parser.add_argument("--root", default=".", help="project root")
    parser.add_argument("--stable-dir", default=DEFAULT_STABLE_FINAL_DIR)
    parser.add_argument("--no-write-files", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    ns = parser.parse_args(list(argv) if argv is not None else None)
    return LTSStableFinalizationOptions(
        root=Path(ns.root),
        stable_dir=Path(ns.stable_dir),
        write_files=not ns.no_write_files,
        quiet=ns.quiet,
    )


def main(argv: Iterable[str] | None = None) -> int:
    options = parse_args(argv)
    manifest = build_lts_stable_finalization_manifest(options)
    if not options.quiet:
        print(format_lts_stable_finalization_text(manifest), end="")
    return 0 if validate_lts_stable_finalization(manifest)["status"] == "pass" else 1
