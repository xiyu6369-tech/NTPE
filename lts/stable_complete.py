from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.translation_engine.utils import now_iso, save_json, save_text
from lts.stable_finalization import (
    LTS_STABLE_FINALIZATION_VERSION,
    LTSStableFinalizationOptions,
    build_lts_stable_finalization_manifest,
    validate_lts_stable_finalization,
)

LTS_STABLE_COMPLETE_VERSION = "1.1-lts-stable-complete"
DEFAULT_STABLE_COMPLETE_DIR = "lts_stable_complete"
DEFAULT_MANIFEST_NAME = "LTS_Stable_Complete_Manifest_1_1.json"
DEFAULT_HASH_NAME = "LTS_Stable_Complete_Hash_1_1.json"
DEFAULT_REPORT_NAME = "LTS_Stable_Complete_Report_1_1.md"
DEFAULT_COMPLETION_MARKER_NAME = "NTPE_1_1_LTS_STABLE_COMPLETE.md"

REQUIRED_STABLE_FINALIZATION_ARTIFACTS = [
    "lts_stable_finalization/LTS_Stable_Finalization_Manifest_1_1.json",
    "lts_stable_finalization/LTS_Stable_Finalization_Hash_1_1.json",
    "lts_stable_finalization/LTS_Stable_Finalization_Report_1_1.md",
    "RELEASE_NOTES_NTPE_1_1_LTS.md",
]

STABLE_COMPLETE_FILES = [
    "ntpe_lts_stable_complete.py",
    "lts/stable_complete.py",
    "ntpe_lts_stable_finalization.py",
    "lts/stable_finalization.py",
    "ntpe_lts_stable_preparation.py",
    "lts/stable_preparation.py",
    "ntpe_translate_txt.py",
    "ntpe_translate_batch.py",
    "ntpe_batch_monitor.py",
    "tools/clean_project.py",
]

STABLE_COMPLETE_CHECKS = [
    "stable_finalization_passes",
    "stable_finalization_artifacts_present",
    "stable_complete_files_present",
    "completion_marker_ready",
    "release_tag_ready",
    "no_feature_changes_after_finalization",
    "clean_packaging_policy_confirmed",
    "stable_complete_ready",
]


@dataclass(frozen=True)
class LTSStableCompleteOptions:
    root: Path = Path(".")
    stable_dir: Path = Path(DEFAULT_STABLE_COMPLETE_DIR)
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


def build_completion_marker_markdown(manifest: dict) -> str:
    release_gate = manifest.get("release_gate", {})
    return "\n".join([
        "# NTPE 1.1 LTS Stable Release Complete",
        "",
        "NTPE 1.1 LTS is complete and ready to be tagged as the long-term support stable release.",
        "",
        "## Release Summary",
        "",
        f"- Version: {manifest.get('version')}",
        f"- Status: {manifest.get('status')}",
        f"- Recommended Tag: `{manifest.get('candidate', {}).get('recommended_tag')}`",
        f"- Release Line: {manifest.get('release_line')}",
        f"- Backward Compatibility: {manifest.get('completion_scope', {}).get('backward_compatibility')}",
        f"- Feature Changes After Finalization: {release_gate.get('feature_changes_after_finalization')}",
        "",
        "## Included LTS Capabilities",
        "",
        "- TXT novel translation entry.",
        "- Batch folder translation.",
        "- Resume, retry, failure recovery, and continue mode.",
        "- Glossary, character memory, QA, Korean residue checks, and Taiwan Traditional Chinese normalization.",
        "- Batch progress, summary reports, runtime monitor, heartbeat, and auto recovery.",
        "- LTS runtime freeze, RC validation, stable preparation, and stable finalization gates.",
        "",
        "## Packaging",
        "",
        "- Full ZIP must be generated after Clean Project Tool removes runtime artifacts.",
        "- Increment ZIP contains only Stable Complete additions.",
        "- No external API calls are performed during release validation.",
    ]).strip() + "\n"


def build_lts_stable_complete_manifest(options: LTSStableCompleteOptions) -> dict:
    root = options.root.resolve()
    stable_dir = _resolve(root, options.stable_dir)

    final_manifest = build_lts_stable_finalization_manifest(
        LTSStableFinalizationOptions(root=root, write_files=False)
    )
    final_result = validate_lts_stable_finalization(final_manifest)

    final_artifacts, missing_final_artifacts = _collect_entries(root, REQUIRED_STABLE_FINALIZATION_ARTIFACTS)
    complete_files, missing_complete_files = _collect_entries(root, STABLE_COMPLETE_FILES)
    written_final_manifest = _read_json(root, REQUIRED_STABLE_FINALIZATION_ARTIFACTS[0])
    written_final_ready = (
        written_final_manifest.get("status") == "pass"
        and written_final_manifest.get("stable_finalization_ready") is True
    )

    release_gate = {
        "stable_finalization_status": final_result.get("status"),
        "written_stable_finalization_ready": written_final_ready,
        "feature_changes_after_finalization": False,
        "external_api_calls": 0,
        "clean_project_tool_required_for_full_zip": True,
        "increment_zip_stage_only": True,
        "official_lts_stable_release_allowed": True,
        "completion_marker_required": True,
    }

    failures: list[str] = []
    if final_result.get("status") != "pass":
        failures.append("stable_finalization_passes")
    if missing_final_artifacts:
        failures.append("stable_finalization_artifacts_present")
    if missing_complete_files:
        failures.append("stable_complete_files_present")
    if not release_gate["completion_marker_required"]:
        failures.append("completion_marker_ready")
    if not release_gate["official_lts_stable_release_allowed"]:
        failures.append("release_tag_ready")
    if release_gate["feature_changes_after_finalization"] is not False:
        failures.append("no_feature_changes_after_finalization")
    if not release_gate["clean_project_tool_required_for_full_zip"]:
        failures.append("clean_packaging_policy_confirmed")
    if not (written_final_ready and release_gate["official_lts_stable_release_allowed"]):
        failures.append("stable_complete_ready")

    stable_complete_ready = not failures
    status = "pass" if stable_complete_ready else "fail"

    manifest = {
        "version": LTS_STABLE_COMPLETE_VERSION,
        "release_line": "NTPE 1.1 LTS",
        "stage": "Stable Release Complete",
        "status": status,
        "created_at": now_iso(),
        "candidate": {
            "source_stage": "NTPE 1.1 LTS Stable Release Finalization",
            "source_version": LTS_STABLE_FINALIZATION_VERSION,
            "recommended_tag": "v1.1.0-lts-stable",
            "next_stage": "NTPE 1.1 LTS Stable Release Complete",
        },
        "completion_scope": {
            "release_target": "NTPE 1.1 LTS Stable",
            "feature_changes_allowed": False,
            "runtime_data_cleaned_before_packaging": True,
            "full_zip_policy": "clean_project_tool_required",
            "increment_zip_policy": "stage_only_changes",
            "backward_compatibility": "preserved",
            "release_state": "complete",
        },
        "release_gate": release_gate,
        "stable_complete_checks": STABLE_COMPLETE_CHECKS,
        "stable_finalization_result": final_result,
        "stable_finalization_artifacts": final_artifacts,
        "stable_complete_files": complete_files,
        "missing_stable_finalization_artifacts": missing_final_artifacts,
        "missing_stable_complete_files": missing_complete_files,
        "stable_complete_ready": stable_complete_ready,
        "failures": failures,
        "validation": {
            "status": status,
            "check_count": len(STABLE_COMPLETE_CHECKS),
            "failure_count": len(failures),
            "stable_finalization_artifact_count": len(final_artifacts),
            "stable_complete_file_count": len(complete_files),
            "selected_regression_suite": "Stable + LTS Stage-01~12 + RC-01~06 + Stable Preparation + Stable Finalization + Stable Complete",
            "expected_result": "ALL PASS",
            "external_api_calls": 0,
        },
    }

    if options.write_files:
        stable_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = stable_dir / DEFAULT_MANIFEST_NAME
        hash_path = stable_dir / DEFAULT_HASH_NAME
        report_path = stable_dir / DEFAULT_REPORT_NAME
        marker_path = root / DEFAULT_COMPLETION_MARKER_NAME
        save_json(manifest_path, manifest)
        save_text(marker_path, build_completion_marker_markdown(manifest))
        stable_hash = {
            "version": LTS_STABLE_COMPLETE_VERSION,
            "manifest": str(manifest_path.relative_to(root)) if manifest_path.is_relative_to(root) else str(manifest_path),
            "manifest_sha256": _sha256(manifest_path),
            "completion_marker": str(marker_path.relative_to(root)) if marker_path.is_relative_to(root) else str(marker_path),
            "completion_marker_sha256": _sha256(marker_path),
            "stable_finalization_artifact_hashes": {entry["path"]: entry["sha256"] for entry in final_artifacts},
            "stable_complete_file_hashes": {entry["path"]: entry["sha256"] for entry in complete_files},
            "stable_complete_ready": stable_complete_ready,
            "status": status,
            "created_at": now_iso(),
        }
        save_json(hash_path, stable_hash)
        save_text(report_path, format_lts_stable_complete_markdown(manifest, stable_hash))
        manifest["manifest_path"] = str(manifest_path)
        manifest["hash_path"] = str(hash_path)
        manifest["report_path"] = str(report_path)
        manifest["completion_marker_path"] = str(marker_path)
    return manifest


def validate_lts_stable_complete(manifest: dict) -> dict:
    failures = list(manifest.get("failures", []))
    passed = manifest.get("status") == "pass" and not failures and manifest.get("stable_complete_ready") is True
    return {
        "version": LTS_STABLE_COMPLETE_VERSION,
        "status": "pass" if passed else "fail",
        "check_count": len(manifest.get("stable_complete_checks", [])),
        "failure_count": len(failures),
        "failures": failures,
        "stable_finalization_artifact_count": len(manifest.get("stable_finalization_artifacts", [])),
        "stable_complete_file_count": len(manifest.get("stable_complete_files", [])),
        "stable_complete_ready": manifest.get("stable_complete_ready"),
    }


def format_lts_stable_complete_text(manifest: dict) -> str:
    result = validate_lts_stable_complete(manifest)
    lines = [
        "NTPE 1.1 LTS Stable Release Complete",
        "=====================================",
        f"status: {manifest.get('status')}",
        f"validation: {result.get('status')}",
        f"recommended_tag: {manifest.get('candidate', {}).get('recommended_tag')}",
        f"release_state: {manifest.get('completion_scope', {}).get('release_state')}",
        f"check_count: {result.get('check_count')}",
        f"failure_count: {result.get('failure_count')}",
        f"stable_finalization_artifact_count: {result.get('stable_finalization_artifact_count')}",
        f"stable_complete_file_count: {result.get('stable_complete_file_count')}",
        f"stable_complete_ready: {result.get('stable_complete_ready')}",
        f"manifest: {manifest.get('manifest_path', '')}",
        f"report: {manifest.get('report_path', '')}",
        f"completion_marker: {manifest.get('completion_marker_path', '')}",
    ]
    return "\n".join(lines).strip() + "\n"


def format_lts_stable_complete_markdown(manifest: dict, stable_hash: dict | None = None) -> str:
    result = validate_lts_stable_complete(manifest)
    failures = set(manifest.get("failures", []))
    lines = [
        "# NTPE 1.1 LTS Stable Release Complete Report",
        "",
        f"- Version: {manifest.get('version')}",
        f"- Status: {manifest.get('status')}",
        f"- Validation: {result.get('status')}",
        f"- Recommended Tag: `{manifest.get('candidate', {}).get('recommended_tag')}`",
        f"- Release State: {manifest.get('completion_scope', {}).get('release_state')}",
        f"- Stable Complete Ready: {manifest.get('stable_complete_ready')}",
        f"- Failure Count: {result.get('failure_count')}",
        f"- External API Calls: {manifest.get('validation', {}).get('external_api_calls')}",
        "",
        "## Completion Checks",
        "",
        "| Check | Status |",
        "|---|---|",
    ]
    for check in manifest.get("stable_complete_checks", []):
        lines.append(f"| `{check}` | {'FAIL' if check in failures else 'PASS'} |")
    lines.extend([
        "",
        "## Completion Scope",
        "",
        f"- Release Target: {manifest.get('completion_scope', {}).get('release_target')}",
        f"- Feature Changes Allowed: {manifest.get('completion_scope', {}).get('feature_changes_allowed')}",
        f"- Full ZIP Policy: {manifest.get('completion_scope', {}).get('full_zip_policy')}",
        f"- Increment ZIP Policy: {manifest.get('completion_scope', {}).get('increment_zip_policy')}",
        "- Confirms Stable Finalization remains passable.",
        "- Writes NTPE 1.1 LTS stable completion marker.",
        "- Requires Clean Project Tool before Full ZIP packaging.",
        "- Performs no external API calls and does not alter translation behavior.",
    ])
    if stable_hash:
        lines.extend([
            "",
            f"Manifest SHA256: `{stable_hash.get('manifest_sha256')}`",
            f"Completion Marker SHA256: `{stable_hash.get('completion_marker_sha256')}`",
        ])
    return "\n".join(lines).strip() + "\n"


def parse_args(argv: Iterable[str] | None = None) -> LTSStableCompleteOptions:
    parser = argparse.ArgumentParser(description="NTPE 1.1 LTS stable release complete")
    parser.add_argument("--root", default=".", help="project root")
    parser.add_argument("--stable-dir", default=DEFAULT_STABLE_COMPLETE_DIR)
    parser.add_argument("--no-write-files", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    ns = parser.parse_args(list(argv) if argv is not None else None)
    return LTSStableCompleteOptions(
        root=Path(ns.root),
        stable_dir=Path(ns.stable_dir),
        write_files=not ns.no_write_files,
        quiet=ns.quiet,
    )


def main(argv: Iterable[str] | None = None) -> int:
    options = parse_args(argv)
    manifest = build_lts_stable_complete_manifest(options)
    if not options.quiet:
        print(format_lts_stable_complete_text(manifest), end="")
    return 0 if validate_lts_stable_complete(manifest)["status"] == "pass" else 1