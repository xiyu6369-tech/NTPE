from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.translation_engine.utils import now_iso, save_json, save_text
from lts.final_validation import (
    LTS_RC_FINAL_VERSION,
    LTSRCFinalValidationOptions,
    build_lts_rc_final_validation_manifest,
    validate_lts_rc_final_validation,
)

LTS_RC_FREEZE_VERSION = "1.1-lts-rc-06"
DEFAULT_FREEZE_DIR = "lts_rc_freeze"
DEFAULT_MANIFEST_NAME = "LTS_RC_06_Freeze_Manifest_1_1.json"
DEFAULT_HASH_NAME = "LTS_RC_06_Freeze_Hash_1_1.json"
DEFAULT_REPORT_NAME = "LTS_RC_06_Freeze_Report_1_1.md"

REQUIRED_FINAL_ARTIFACTS = [
    "lts_rc_final_validation/LTS_RC_05_Final_Validation_Manifest_1_1.json",
    "lts_rc_final_validation/LTS_RC_05_Final_Validation_Hash_1_1.json",
    "lts_rc_final_validation/LTS_RC_05_Final_Validation_Report_1_1.md",
]

FREEZE_FILES = [
    "ntpe_lts_rc_freeze.py",
    "lts/rc_freeze.py",
    "ntpe_lts_rc_final_validation.py",
    "lts/final_validation.py",
    "ntpe_lts_release_candidate.py",
    "lts/release_candidate.py",
    "ntpe_lts_runtime_freeze.py",
    "lts/runtime_freeze.py",
]

FREEZE_CHECKS = [
    "rc05_final_validation_passes",
    "final_validation_artifacts_present",
    "freeze_files_present",
    "lts_runtime_freeze_preserved",
    "frozen_compatibility_policy_preserved",
    "rc_freeze_ready",
]


@dataclass(frozen=True)
class LTSRCFreezeOptions:
    root: Path = Path(".")
    freeze_dir: Path = Path(DEFAULT_FREEZE_DIR)
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


def build_lts_rc_freeze_manifest(options: LTSRCFreezeOptions) -> dict:
    root = options.root.resolve()
    freeze_dir = _resolve(root, options.freeze_dir)

    rc05_manifest = build_lts_rc_final_validation_manifest(
        LTSRCFinalValidationOptions(root=root, write_files=False)
    )
    rc05_result = validate_lts_rc_final_validation(rc05_manifest)

    final_artifacts, missing_final_artifacts = _collect_entries(root, REQUIRED_FINAL_ARTIFACTS)
    freeze_files, missing_freeze_files = _collect_entries(root, FREEZE_FILES)

    runtime_freeze_manifest = _read_json(
        root, "lts_runtime_freeze/LTS_Runtime_Freeze_Manifest_1_1.json"
    )
    lts_runtime_freeze_preserved = runtime_freeze_manifest.get("status") in {"pass", "frozen"}

    compatibility_policy = rc05_manifest.get("compatibility_policy", {})
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

    failures: list[str] = []
    if rc05_result.get("status") != "pass":
        failures.append("rc05_final_validation_passes")
    if missing_final_artifacts:
        failures.append("final_validation_artifacts_present")
    if missing_freeze_files:
        failures.append("freeze_files_present")
    if not lts_runtime_freeze_preserved:
        failures.append("lts_runtime_freeze_preserved")
    if not frozen_policy_preserved:
        failures.append("frozen_compatibility_policy_preserved")

    rc_freeze_ready = not failures
    if not rc_freeze_ready:
        failures.append("rc_freeze_ready")

    status = "pass" if not failures else "fail"
    manifest = {
        "version": LTS_RC_FREEZE_VERSION,
        "release_line": "NTPE 1.1 LTS",
        "stage": "RC-06 LTS RC Freeze",
        "status": status,
        "created_at": now_iso(),
        "candidate": {
            "source_stage": "RC-05 Release Candidate Final Validation",
            "source_version": LTS_RC_FINAL_VERSION,
            "recommended_tag": "v1.1.0-lts-rc-06-freeze",
            "next_stage": "NTPE 1.1 LTS Stable Release Preparation",
        },
        "freeze_scope": {
            "frozen_runtime": "NTPE 1.1 LTS Runtime",
            "frozen_rc_chain": "RC-01 through RC-05",
            "feature_changes_allowed": False,
            "external_api_calls": 0,
            "runtime_data_cleaned_before_packaging": True,
        },
        "rc05_result": rc05_result,
        "freeze_checks": FREEZE_CHECKS,
        "final_validation_artifacts": final_artifacts,
        "freeze_files": freeze_files,
        "missing_final_validation_artifacts": missing_final_artifacts,
        "missing_freeze_files": missing_freeze_files,
        "compatibility_policy": compatibility_policy,
        "lts_runtime_freeze_preserved": lts_runtime_freeze_preserved,
        "frozen_policy_preserved": frozen_policy_preserved,
        "rc_freeze_ready": rc_freeze_ready,
        "failures": failures,
        "validation": {
            "status": status,
            "check_count": len(FREEZE_CHECKS),
            "failure_count": len(failures),
            "final_artifact_count": len(final_artifacts),
            "freeze_file_count": len(freeze_files),
            "selected_regression_suite": "Stable + LTS Stage-01~12 + RC-01~06",
            "expected_result": "ALL PASS",
            "external_api_calls": 0,
        },
    }

    if options.write_files:
        freeze_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = freeze_dir / DEFAULT_MANIFEST_NAME
        hash_path = freeze_dir / DEFAULT_HASH_NAME
        report_path = freeze_dir / DEFAULT_REPORT_NAME
        save_json(manifest_path, manifest)
        freeze_hash = {
            "version": LTS_RC_FREEZE_VERSION,
            "manifest": str(manifest_path.relative_to(root)) if manifest_path.is_relative_to(root) else str(manifest_path),
            "manifest_sha256": _sha256(manifest_path),
            "final_validation_artifact_hashes": {entry["path"]: entry["sha256"] for entry in final_artifacts},
            "freeze_file_hashes": {entry["path"]: entry["sha256"] for entry in freeze_files},
            "rc_freeze_ready": rc_freeze_ready,
            "status": status,
            "created_at": now_iso(),
        }
        save_json(hash_path, freeze_hash)
        save_text(report_path, format_lts_rc_freeze_markdown(manifest, freeze_hash))
        manifest["manifest_path"] = str(manifest_path)
        manifest["hash_path"] = str(hash_path)
        manifest["report_path"] = str(report_path)
    return manifest


def validate_lts_rc_freeze(manifest: dict) -> dict:
    failures = list(manifest.get("failures", []))
    passed = manifest.get("status") == "pass" and not failures and manifest.get("rc_freeze_ready") is True
    return {
        "version": LTS_RC_FREEZE_VERSION,
        "status": "pass" if passed else "fail",
        "check_count": len(manifest.get("freeze_checks", [])),
        "failure_count": len(failures),
        "failures": failures,
        "final_artifact_count": len(manifest.get("final_validation_artifacts", [])),
        "freeze_file_count": len(manifest.get("freeze_files", [])),
        "rc_freeze_ready": manifest.get("rc_freeze_ready"),
    }


def format_lts_rc_freeze_text(manifest: dict) -> str:
    result = validate_lts_rc_freeze(manifest)
    lines = [
        "NTPE 1.1 LTS RC-06 LTS RC Freeze",
        "===================================",
        f"status: {manifest.get('status')}",
        f"validation: {result.get('status')}",
        f"recommended_tag: {manifest.get('candidate', {}).get('recommended_tag')}",
        f"next_stage: {manifest.get('candidate', {}).get('next_stage')}",
        f"check_count: {result.get('check_count')}",
        f"failure_count: {result.get('failure_count')}",
        f"final_artifact_count: {result.get('final_artifact_count')}",
        f"freeze_file_count: {result.get('freeze_file_count')}",
        f"rc_freeze_ready: {result.get('rc_freeze_ready')}",
        f"manifest: {manifest.get('manifest_path', '')}",
        f"report: {manifest.get('report_path', '')}",
    ]
    return "\n".join(lines).strip() + "\n"


def format_lts_rc_freeze_markdown(manifest: dict, freeze_hash: dict | None = None) -> str:
    result = validate_lts_rc_freeze(manifest)
    failures = set(manifest.get("failures", []))
    lines = [
        "# NTPE 1.1 LTS RC-06 LTS RC Freeze Report",
        "",
        f"- Version: {manifest.get('version')}",
        f"- Status: {manifest.get('status')}",
        f"- Validation: {result.get('status')}",
        f"- Recommended Tag: `{manifest.get('candidate', {}).get('recommended_tag')}`",
        f"- Next Stage: {manifest.get('candidate', {}).get('next_stage')}",
        f"- RC Freeze Ready: {manifest.get('rc_freeze_ready')}",
        f"- Failure Count: {result.get('failure_count')}",
        f"- External API Calls: {manifest.get('validation', {}).get('external_api_calls')}",
        "",
        "## Freeze Checks",
        "",
        "| Check | Status |",
        "|---|---|",
    ]
    for check in manifest.get("freeze_checks", []):
        lines.append(f"| `{check}` | {'FAIL' if check in failures else 'PASS'} |")
    lines.extend([
        "",
        "## Freeze Scope",
        "",
        f"- Frozen Runtime: {manifest.get('freeze_scope', {}).get('frozen_runtime')}",
        f"- Frozen RC Chain: {manifest.get('freeze_scope', {}).get('frozen_rc_chain')}",
        f"- Feature Changes Allowed: {manifest.get('freeze_scope', {}).get('feature_changes_allowed')}",
        "- Confirms RC-05 final validation remains passable.",
        "- Preserves NTPE 1.0 Stable and LTS Runtime frozen compatibility policies.",
        "- Performs no external API calls and does not alter translation behavior.",
    ])
    if freeze_hash:
        lines.extend(["", f"Manifest SHA256: `{freeze_hash.get('manifest_sha256')}`"])
    return "\n".join(lines).strip() + "\n"


def parse_args(argv: Iterable[str] | None = None) -> LTSRCFreezeOptions:
    parser = argparse.ArgumentParser(description="NTPE 1.1 LTS RC-06 LTS RC freeze")
    parser.add_argument("--root", default=".", help="project root")
    parser.add_argument("--freeze-dir", default=DEFAULT_FREEZE_DIR)
    parser.add_argument("--no-write-files", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    ns = parser.parse_args(list(argv) if argv is not None else None)
    return LTSRCFreezeOptions(
        root=Path(ns.root),
        freeze_dir=Path(ns.freeze_dir),
        write_files=not ns.no_write_files,
        quiet=ns.quiet,
    )


def main(argv: Iterable[str] | None = None) -> int:
    options = parse_args(argv)
    manifest = build_lts_rc_freeze_manifest(options)
    if not options.quiet:
        print(format_lts_rc_freeze_text(manifest), end="")
    return 0 if validate_lts_rc_freeze(manifest)["status"] == "pass" else 1
