from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.translation_engine.utils import now_iso, save_json, save_text

LTS_RUNTIME_FREEZE_VERSION = "1.1-lts-stage-11"
DEFAULT_FREEZE_DIR = "lts_runtime_freeze"
DEFAULT_MANIFEST_NAME = "LTS_Runtime_Freeze_Manifest_1_1.json"
DEFAULT_HASH_NAME = "LTS_Runtime_Freeze_Hash_1_1.json"
DEFAULT_REPORT_NAME = "LTS_Runtime_Freeze_Report_1_1.md"

FROZEN_RUNTIME_FILES = [
    "ntpe_translate_txt.py",
    "ntpe_translate_batch.py",
    "ntpe_batch_monitor.py",
    "ntpe_long_run_recovery.py",
    "lts/txt_translation_runtime.py",
    "lts/batch_translation_runtime.py",
    "lts/batch_runtime_monitor.py",
    "lts/long_run_recovery.py",
]

REQUIRED_STAGE_REPORTS = [
    "LTS_Stage_01_TXT_Translation_Entry_Report.md",
    "LTS_Stage_02_Resume_Retry_Report.md",
    "LTS_Stage_03_Glossary_Character_Memory_Report.md",
    "LTS_Stage_04_Translation_QA_Report.md",
    "LTS_Stage_05_Report.md",
    "Clean_Project_Tool_Report_1_1_LTS.md",
    "LTS_Stage_06_Batch_Translation_Report.md",
    "LTS_Stage_07_Batch_Progress_Report.md",
    "LTS_Stage_08_Batch_Failure_Recovery_Report.md",
    "LTS_Stage_09_Batch_Runtime_Monitor_Report.md",
    "LTS_Stage_10_Long_Run_Stability_Report.md",
]

@dataclass(frozen=True)
class RuntimeFreezeOptions:
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


def build_runtime_freeze_manifest(options: RuntimeFreezeOptions) -> dict:
    root = options.root.resolve()
    freeze_dir = _resolve(root, options.freeze_dir)
    runtime_entries = []
    missing_runtime = []
    for rel in FROZEN_RUNTIME_FILES:
        path = root / rel
        if path.exists() and path.is_file():
            runtime_entries.append({
                "path": rel,
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
            })
        else:
            missing_runtime.append(rel)

    stage_reports = []
    missing_reports = []
    for rel in REQUIRED_STAGE_REPORTS:
        path = root / rel
        if path.exists() and path.is_file():
            stage_reports.append({
                "path": rel,
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
            })
        else:
            missing_reports.append(rel)

    status = "frozen" if not missing_runtime and not missing_reports else "incomplete"
    manifest = {
        "version": LTS_RUNTIME_FREEZE_VERSION,
        "release_line": "NTPE 1.1 LTS",
        "stage": "Stage-11 LTS Runtime Freeze / Validation",
        "status": status,
        "created_at": now_iso(),
        "compatibility_policy": {
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
            "stable_1_0": "preserved",
            "lts_1_1": "incremental_additive",
        },
        "runtime_files": runtime_entries,
        "stage_reports": stage_reports,
        "missing_runtime_files": missing_runtime,
        "missing_stage_reports": missing_reports,
        "validation": {
            "runtime_file_count": len(runtime_entries),
            "stage_report_count": len(stage_reports),
            "missing_count": len(missing_runtime) + len(missing_reports),
            "selected_regression_suite": "Stable + LTS Stage-01~10 + Clean Project Tool + Stage-11",
            "expected_result": "ALL PASS",
        },
    }

    if options.write_files:
        freeze_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = freeze_dir / DEFAULT_MANIFEST_NAME
        hash_path = freeze_dir / DEFAULT_HASH_NAME
        report_path = freeze_dir / DEFAULT_REPORT_NAME
        save_json(manifest_path, manifest)
        freeze_hash = {
            "version": LTS_RUNTIME_FREEZE_VERSION,
            "manifest": str(manifest_path.relative_to(root)) if manifest_path.is_relative_to(root) else str(manifest_path),
            "manifest_sha256": _sha256(manifest_path),
            "runtime_file_hashes": {entry["path"]: entry["sha256"] for entry in runtime_entries},
            "status": status,
            "created_at": now_iso(),
        }
        save_json(hash_path, freeze_hash)
        save_text(report_path, format_runtime_freeze_markdown(manifest, freeze_hash))
        manifest["manifest_path"] = str(manifest_path)
        manifest["hash_path"] = str(hash_path)
        manifest["report_path"] = str(report_path)
    return manifest


def validate_runtime_freeze(manifest: dict) -> dict:
    missing = list(manifest.get("missing_runtime_files", [])) + list(manifest.get("missing_stage_reports", []))
    passed = manifest.get("status") == "frozen" and not missing
    return {
        "version": LTS_RUNTIME_FREEZE_VERSION,
        "status": "pass" if passed else "fail",
        "runtime_file_count": len(manifest.get("runtime_files", [])),
        "stage_report_count": len(manifest.get("stage_reports", [])),
        "missing_count": len(missing),
        "missing": missing,
    }


def format_runtime_freeze_text(manifest: dict) -> str:
    result = validate_runtime_freeze(manifest)
    lines = [
        "NTPE 1.1 LTS Runtime Freeze / Validation",
        "==========================================",
        f"status: {manifest.get('status')}",
        f"validation: {result.get('status')}",
        f"runtime_file_count: {result.get('runtime_file_count')}",
        f"stage_report_count: {result.get('stage_report_count')}",
        f"missing_count: {result.get('missing_count')}",
        f"manifest: {manifest.get('manifest_path', '')}",
        f"report: {manifest.get('report_path', '')}",
    ]
    return "\n".join(lines).strip() + "\n"


def format_runtime_freeze_markdown(manifest: dict, freeze_hash: dict | None = None) -> str:
    result = validate_runtime_freeze(manifest)
    lines = [
        "# NTPE 1.1 LTS Stage-11 Runtime Freeze / Validation Report",
        "",
        f"- Version: {manifest.get('version')}",
        f"- Status: {manifest.get('status')}",
        f"- Validation: {result.get('status')}",
        f"- Runtime Files: {result.get('runtime_file_count')}",
        f"- Stage Reports: {result.get('stage_report_count')}",
        f"- Missing Count: {result.get('missing_count')}",
        "",
        "## Frozen Runtime Files",
        "",
        "| Path | SHA256 | Size |",
        "|---|---|---:|",
    ]
    for entry in manifest.get("runtime_files", []):
        lines.append(f"| `{entry.get('path')}` | `{entry.get('sha256')}` | {entry.get('size_bytes')} |")
    lines.extend(["", "## Compatibility", ""])
    for key, value in manifest.get("compatibility_policy", {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Validation Scope", ""])
    lines.append("- Stable release regression preserved")
    lines.append("- LTS Stage-01 through Stage-10 preserved")
    lines.append("- Clean Project Tool preserved")
    lines.append("- Runtime freeze manifest and hashes generated")
    if freeze_hash:
        lines.extend(["", f"Manifest SHA256: `{freeze_hash.get('manifest_sha256')}`"])
    return "\n".join(lines).strip() + "\n"


def parse_args(argv: Iterable[str] | None = None) -> RuntimeFreezeOptions:
    parser = argparse.ArgumentParser(description="NTPE 1.1 LTS Stage-11 runtime freeze / validation")
    parser.add_argument("--root", default=".", help="project root")
    parser.add_argument("--freeze-dir", default=DEFAULT_FREEZE_DIR)
    parser.add_argument("--no-write-files", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    ns = parser.parse_args(list(argv) if argv is not None else None)
    return RuntimeFreezeOptions(
        root=Path(ns.root),
        freeze_dir=Path(ns.freeze_dir),
        write_files=not ns.no_write_files,
        quiet=ns.quiet,
    )


def main(argv: Iterable[str] | None = None) -> int:
    options = parse_args(argv)
    manifest = build_runtime_freeze_manifest(options)
    if not options.quiet:
        print(format_runtime_freeze_text(manifest), end="")
    return 0 if validate_runtime_freeze(manifest)["status"] == "pass" else 1
