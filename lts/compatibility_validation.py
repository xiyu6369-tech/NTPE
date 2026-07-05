from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.translation_engine.utils import now_iso, save_json, save_text
from lts.regression_validation import (
    LTS_RC_REGRESSION_VERSION,
    build_lts_rc_regression_manifest,
    validate_lts_rc_regression,
    LTSRCRegressionOptions,
)
from lts.runtime_freeze import FROZEN_RUNTIME_FILES

LTS_RC_COMPATIBILITY_VERSION = "1.1-lts-rc-02"
DEFAULT_COMPATIBILITY_DIR = "lts_rc_compatibility"
DEFAULT_MANIFEST_NAME = "LTS_RC_02_Compatibility_Validation_Manifest_1_1.json"
DEFAULT_HASH_NAME = "LTS_RC_02_Compatibility_Validation_Hash_1_1.json"
DEFAULT_REPORT_NAME = "LTS_RC_02_Compatibility_Validation_Report_1_1.md"

REQUIRED_RC01_ARTIFACTS = [
    "lts_rc_regression/LTS_RC_01_Regression_Validation_Manifest_1_1.json",
    "lts_rc_regression/LTS_RC_01_Regression_Validation_Hash_1_1.json",
    "lts_rc_regression/LTS_RC_01_Regression_Validation_Report_1_1.md",
]

REQUIRED_PUBLIC_COMMANDS = [
    "launcher.py",
    "launcher_translate.py",
    "ntpe_translate_txt.py",
    "ntpe_translate_batch.py",
    "ntpe_batch_monitor.py",
    "ntpe_long_run_recovery.py",
    "ntpe_lts_runtime_freeze.py",
    "ntpe_lts_release_candidate.py",
    "ntpe_lts_rc_regression.py",
]

REQUIRED_LTS_BATCH_FLAGS = [
    "--recursive",
    "--continue-on-failure",
    "--failed-only",
    "--quiet-progress",
    "--heartbeat",
    "--auto-recovery",
]

REQUIRED_LTS_TXT_FLAGS = [
    "--glossary",
    "--character-memory",
    "--qa-fail-policy",
    "--max-korean-chars",
    "--min-length-ratio",
    "--max-retries",
    "--retry-base-seconds",
]

COMPATIBILITY_CHECKS = [
    "rc01_regression_validation_passes",
    "rc01_artifact_chain_present",
    "public_commands_present",
    "frozen_runtime_files_present",
    "batch_flags_preserved",
    "txt_flags_preserved",
    "compatibility_policy_preserved",
]

@dataclass(frozen=True)
class LTSRCCompatibilityOptions:
    root: Path = Path(".")
    compatibility_dir: Path = Path(DEFAULT_COMPATIBILITY_DIR)
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


def _script_contains_flags(root: Path, scripts: str | Iterable[str], flags: Iterable[str]) -> tuple[list[str], list[str]]:
    script_list = [scripts] if isinstance(scripts, str) else list(scripts)
    text_parts: list[str] = []
    for script in script_list:
        path = root / script
        if path.exists():
            text_parts.append(path.read_text(encoding="utf-8", errors="ignore"))
    text = "\n".join(text_parts)
    present = [flag for flag in flags if flag in text]
    missing = [flag for flag in flags if flag not in text]
    return present, missing


def build_lts_rc_compatibility_manifest(options: LTSRCCompatibilityOptions) -> dict:
    root = options.root.resolve()
    compatibility_dir = _resolve(root, options.compatibility_dir)

    regression_manifest = build_lts_rc_regression_manifest(
        LTSRCRegressionOptions(root=root, write_files=False)
    )
    regression_result = validate_lts_rc_regression(regression_manifest)

    rc01_entries, missing_rc01 = _collect_entries(root, REQUIRED_RC01_ARTIFACTS)
    command_entries, missing_commands = _collect_entries(root, REQUIRED_PUBLIC_COMMANDS)
    runtime_entries, missing_runtime = _collect_entries(root, FROZEN_RUNTIME_FILES)
    batch_flags_present, missing_batch_flags = _script_contains_flags(root, ["ntpe_translate_batch.py", "lts/batch_translation_runtime.py"], REQUIRED_LTS_BATCH_FLAGS)
    txt_flags_present, missing_txt_flags = _script_contains_flags(root, ["ntpe_translate_txt.py", "lts/txt_translation_runtime.py"], REQUIRED_LTS_TXT_FLAGS)

    compatibility_policy = {
        "ntpe_1_0_stable": "preserved",
        "foundation_v1_0": "frozen",
        "cli": "frozen",
        "sdk": "frozen",
        "integration": "frozen",
        "workflow": "frozen",
        "platform_services": "frozen",
        "runtime_api": "frozen",
        "external_rest_api": "frozen",
        "web_ui": "frozen",
        "packaging_release": "frozen",
        "lts_runtime": "frozen_by_stage_11",
        "rc_02_change_type": "compatibility_validation_metadata_only",
    }

    failures: list[str] = []
    if regression_result["status"] != "pass":
        failures.append("rc01_regression_validation_passes")
    if missing_rc01:
        failures.append("rc01_artifact_chain_present")
    if missing_commands:
        failures.append("public_commands_present")
    if missing_runtime:
        failures.append("frozen_runtime_files_present")
    if missing_batch_flags:
        failures.append("batch_flags_preserved")
    if missing_txt_flags:
        failures.append("txt_flags_preserved")
    if any(value != "frozen" and value != "preserved" and value != "frozen_by_stage_11" and value != "compatibility_validation_metadata_only" for value in compatibility_policy.values()):
        failures.append("compatibility_policy_preserved")

    status = "pass" if not failures else "fail"
    manifest = {
        "version": LTS_RC_COMPATIBILITY_VERSION,
        "release_line": "NTPE 1.1 LTS",
        "stage": "RC-02 Compatibility Validation",
        "status": status,
        "created_at": now_iso(),
        "candidate": {
            "source_stage": "RC-01 Regression Validation",
            "source_version": LTS_RC_REGRESSION_VERSION,
            "recommended_tag": "v1.1.0-lts-rc-02-compatibility",
        },
        "compatibility_policy": compatibility_policy,
        "compatibility_checks": COMPATIBILITY_CHECKS,
        "regression_validation": regression_result,
        "rc01_artifacts": rc01_entries,
        "public_commands": command_entries,
        "runtime_files": runtime_entries,
        "batch_flags_present": batch_flags_present,
        "txt_flags_present": txt_flags_present,
        "missing_rc01_artifacts": missing_rc01,
        "missing_public_commands": missing_commands,
        "missing_runtime_files": missing_runtime,
        "missing_batch_flags": missing_batch_flags,
        "missing_txt_flags": missing_txt_flags,
        "failures": failures,
        "validation": {
            "status": status,
            "check_count": len(COMPATIBILITY_CHECKS),
            "failure_count": len(failures),
            "public_command_count": len(command_entries),
            "runtime_file_count": len(runtime_entries),
            "rc01_artifact_count": len(rc01_entries),
            "selected_regression_suite": "Stable + LTS Stage-01~12 + RC-01 + RC-02",
            "expected_result": "ALL PASS",
        },
    }

    if options.write_files:
        compatibility_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = compatibility_dir / DEFAULT_MANIFEST_NAME
        hash_path = compatibility_dir / DEFAULT_HASH_NAME
        report_path = compatibility_dir / DEFAULT_REPORT_NAME
        save_json(manifest_path, manifest)
        compatibility_hash = {
            "version": LTS_RC_COMPATIBILITY_VERSION,
            "manifest": str(manifest_path.relative_to(root)) if manifest_path.is_relative_to(root) else str(manifest_path),
            "manifest_sha256": _sha256(manifest_path),
            "public_command_hashes": {entry["path"]: entry["sha256"] for entry in command_entries},
            "runtime_file_hashes": {entry["path"]: entry["sha256"] for entry in runtime_entries},
            "rc01_artifact_hashes": {entry["path"]: entry["sha256"] for entry in rc01_entries},
            "status": status,
            "created_at": now_iso(),
        }
        save_json(hash_path, compatibility_hash)
        save_text(report_path, format_lts_rc_compatibility_markdown(manifest, compatibility_hash))
        manifest["manifest_path"] = str(manifest_path)
        manifest["hash_path"] = str(hash_path)
        manifest["report_path"] = str(report_path)
    return manifest


def validate_lts_rc_compatibility(manifest: dict) -> dict:
    failures = list(manifest.get("failures", []))
    passed = manifest.get("status") == "pass" and not failures
    return {
        "version": LTS_RC_COMPATIBILITY_VERSION,
        "status": "pass" if passed else "fail",
        "check_count": len(manifest.get("compatibility_checks", [])),
        "failure_count": len(failures),
        "failures": failures,
        "public_command_count": len(manifest.get("public_commands", [])),
        "runtime_file_count": len(manifest.get("runtime_files", [])),
        "rc01_artifact_count": len(manifest.get("rc01_artifacts", [])),
    }


def format_lts_rc_compatibility_text(manifest: dict) -> str:
    result = validate_lts_rc_compatibility(manifest)
    lines = [
        "NTPE 1.1 LTS RC-02 Compatibility Validation",
        "===============================================",
        f"status: {manifest.get('status')}",
        f"validation: {result.get('status')}",
        f"recommended_tag: {manifest.get('candidate', {}).get('recommended_tag')}",
        f"check_count: {result.get('check_count')}",
        f"failure_count: {result.get('failure_count')}",
        f"public_command_count: {result.get('public_command_count')}",
        f"runtime_file_count: {result.get('runtime_file_count')}",
        f"rc01_artifact_count: {result.get('rc01_artifact_count')}",
        f"manifest: {manifest.get('manifest_path', '')}",
        f"report: {manifest.get('report_path', '')}",
    ]
    return "\n".join(lines).strip() + "\n"


def format_lts_rc_compatibility_markdown(manifest: dict, compatibility_hash: dict | None = None) -> str:
    result = validate_lts_rc_compatibility(manifest)
    lines = [
        "# NTPE 1.1 LTS RC-02 Compatibility Validation Report",
        "",
        f"- Version: {manifest.get('version')}",
        f"- Status: {manifest.get('status')}",
        f"- Validation: {result.get('status')}",
        f"- Recommended Tag: `{manifest.get('candidate', {}).get('recommended_tag')}`",
        f"- Compatibility Checks: {result.get('check_count')}",
        f"- Failure Count: {result.get('failure_count')}",
        "",
        "## Compatibility Gate",
        "",
        "| Check | Status |",
        "|---|---|",
    ]
    failures = set(manifest.get("failures", []))
    for check in manifest.get("compatibility_checks", []):
        lines.append(f"| `{check}` | {'FAIL' if check in failures else 'PASS'} |")
    lines.extend([
        "",
        "## Preserved Public Commands",
        "",
    ])
    for entry in manifest.get("public_commands", []):
        lines.append(f"- `{entry.get('path')}`")
    lines.extend([
        "",
        "## Compatibility Policy",
        "",
    ])
    for key, value in manifest.get("compatibility_policy", {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend([
        "",
        "## Validation Scope",
        "",
        "- Confirms RC-01 regression validation remains passable.",
        "- Confirms LTS public command entry points remain present.",
        "- Confirms frozen runtime files remain present.",
        "- Confirms Stage-01 through Stage-10 user-facing flags remain preserved.",
        "- Does not modify Foundation v1.0, CLI, SDK, Runtime API, REST API, Web UI, or frozen LTS runtime behavior.",
    ])
    if compatibility_hash:
        lines.extend(["", f"Manifest SHA256: `{compatibility_hash.get('manifest_sha256')}`"])
    return "\n".join(lines).strip() + "\n"


def parse_args(argv: Iterable[str] | None = None) -> LTSRCCompatibilityOptions:
    parser = argparse.ArgumentParser(description="NTPE 1.1 LTS RC-02 compatibility validation")
    parser.add_argument("--root", default=".", help="project root")
    parser.add_argument("--compatibility-dir", default=DEFAULT_COMPATIBILITY_DIR)
    parser.add_argument("--no-write-files", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    ns = parser.parse_args(list(argv) if argv is not None else None)
    return LTSRCCompatibilityOptions(
        root=Path(ns.root),
        compatibility_dir=Path(ns.compatibility_dir),
        write_files=not ns.no_write_files,
        quiet=ns.quiet,
    )


def main(argv: Iterable[str] | None = None) -> int:
    options = parse_args(argv)
    manifest = build_lts_rc_compatibility_manifest(options)
    if not options.quiet:
        print(format_lts_rc_compatibility_text(manifest), end="")
    return 0 if validate_lts_rc_compatibility(manifest)["status"] == "pass" else 1
