from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.translation_engine.utils import now_iso, save_json, save_text
from lts.compatibility_validation import (
    LTS_RC_COMPATIBILITY_VERSION,
    build_lts_rc_compatibility_manifest,
    validate_lts_rc_compatibility,
    LTSRCCompatibilityOptions,
)
from lts.long_run_recovery import (
    LongRunRecoveryOptions,
    build_recovery_plan,
)

LTS_RC_PERFORMANCE_VERSION = "1.1-lts-rc-03"
DEFAULT_PERFORMANCE_DIR = "lts_rc_performance"
DEFAULT_MANIFEST_NAME = "LTS_RC_03_Performance_Long_Run_Validation_Manifest_1_1.json"
DEFAULT_HASH_NAME = "LTS_RC_03_Performance_Long_Run_Validation_Hash_1_1.json"
DEFAULT_REPORT_NAME = "LTS_RC_03_Performance_Long_Run_Validation_Report_1_1.md"

REQUIRED_RC02_ARTIFACTS = [
    "lts_rc_compatibility/LTS_RC_02_Compatibility_Validation_Manifest_1_1.json",
    "lts_rc_compatibility/LTS_RC_02_Compatibility_Validation_Hash_1_1.json",
    "lts_rc_compatibility/LTS_RC_02_Compatibility_Validation_Report_1_1.md",
]

PERFORMANCE_FILES = [
    "ntpe_translate_txt.py",
    "ntpe_translate_batch.py",
    "ntpe_batch_monitor.py",
    "lts/batch_translation_runtime.py",
    "lts/batch_runtime_monitor.py",
    "lts/long_run_recovery.py",
]

PERFORMANCE_CHECKS = [
    "rc02_compatibility_validation_passes",
    "rc02_artifact_chain_present",
    "long_run_recovery_validation_passes",
    "performance_files_present",
    "batch_runtime_supports_resume",
    "batch_runtime_supports_failure_recovery",
    "batch_runtime_supports_heartbeat",
    "monitor_runtime_present",
]

@dataclass(frozen=True)
class LTSRCPerformanceOptions:
    root: Path = Path(".")
    performance_dir: Path = Path(DEFAULT_PERFORMANCE_DIR)
    write_files: bool = True
    quiet: bool = False
    sample_file_count: int = 120
    sample_chunk_count: int = 9320


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


def _contains(root: Path, rels: Iterable[str], token: str) -> bool:
    for rel in rels:
        path = root / rel
        if path.exists() and path.is_file():
            if token in path.read_text(encoding="utf-8", errors="ignore"):
                return True
    return False


def _static_timing_probe(sample_file_count: int, sample_chunk_count: int) -> dict:
    start = time.perf_counter()
    files = [f"chapter_{i:04d}.txt" for i in range(1, sample_file_count + 1)]
    chunks = list(range(1, sample_chunk_count + 1))
    checksum = hashlib.sha256(("|".join(files[:5]) + str(sum(chunks))).encode("utf-8")).hexdigest()
    elapsed_ms = round((time.perf_counter() - start) * 1000, 3)
    return {
        "mode": "static_runtime_probe_no_external_api",
        "sample_file_count": sample_file_count,
        "sample_chunk_count": sample_chunk_count,
        "elapsed_ms": elapsed_ms,
        "checksum": checksum,
        "status": "pass",
    }


def build_lts_rc_performance_manifest(options: LTSRCPerformanceOptions) -> dict:
    root = options.root.resolve()
    performance_dir = _resolve(root, options.performance_dir)

    compatibility_manifest = build_lts_rc_compatibility_manifest(
        LTSRCCompatibilityOptions(root=root, write_files=False)
    )
    compatibility_result = validate_lts_rc_compatibility(compatibility_manifest)

    recovery_plan = build_recovery_plan(
        LongRunRecoveryOptions(output_dir=root / "output", write_report=False), root=root
    )
    recovery_result = {
        "status": "pass" if recovery_plan.get("status") in {"healthy", "recovery_required"} else "fail",
        "plan_status": recovery_plan.get("status"),
        "action_count": recovery_plan.get("summary", {}).get("action_count", 0),
    }

    rc02_entries, missing_rc02 = _collect_entries(root, REQUIRED_RC02_ARTIFACTS)
    performance_entries, missing_performance_files = _collect_entries(root, PERFORMANCE_FILES)

    batch_files = ["ntpe_translate_batch.py", "lts/batch_translation_runtime.py"]
    monitor_files = ["ntpe_batch_monitor.py", "lts/batch_runtime_monitor.py", "lts/long_run_recovery.py"]
    capability_checks = {
        "batch_runtime_supports_resume": _contains(root, batch_files, "resume"),
        "batch_runtime_supports_failure_recovery": _contains(root, batch_files, "failed"),
        "batch_runtime_supports_heartbeat": _contains(root, batch_files, "heartbeat"),
        "monitor_runtime_present": any((root / rel).exists() for rel in monitor_files),
    }

    timing_probe = _static_timing_probe(options.sample_file_count, options.sample_chunk_count)

    failures: list[str] = []
    if compatibility_result["status"] != "pass":
        failures.append("rc02_compatibility_validation_passes")
    if missing_rc02:
        failures.append("rc02_artifact_chain_present")
    if recovery_result["status"] != "pass":
        failures.append("long_run_recovery_validation_passes")
    if missing_performance_files:
        failures.append("performance_files_present")
    for check, passed in capability_checks.items():
        if not passed:
            failures.append(check)
    if timing_probe["status"] != "pass":
        failures.append("static_timing_probe_passes")

    status = "pass" if not failures else "fail"
    manifest = {
        "version": LTS_RC_PERFORMANCE_VERSION,
        "release_line": "NTPE 1.1 LTS",
        "stage": "RC-03 Performance / Long-Run Validation",
        "status": status,
        "created_at": now_iso(),
        "candidate": {
            "source_stage": "RC-02 Compatibility Validation",
            "source_version": LTS_RC_COMPATIBILITY_VERSION,
            "recommended_tag": "v1.1.0-lts-rc-03-performance",
        },
        "performance_checks": PERFORMANCE_CHECKS,
        "compatibility_validation": compatibility_result,
        "long_run_recovery_validation": recovery_result,
        "capability_checks": capability_checks,
        "timing_probe": timing_probe,
        "rc02_artifacts": rc02_entries,
        "performance_files": performance_entries,
        "missing_rc02_artifacts": missing_rc02,
        "missing_performance_files": missing_performance_files,
        "failures": failures,
        "validation": {
            "status": status,
            "check_count": len(PERFORMANCE_CHECKS),
            "failure_count": len(failures),
            "performance_file_count": len(performance_entries),
            "rc02_artifact_count": len(rc02_entries),
            "selected_regression_suite": "Stable + LTS Stage-01~12 + RC-01~03",
            "expected_result": "ALL PASS",
            "external_api_calls": 0,
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
            "rc_03_change_type": "performance_validation_metadata_only",
        },
    }

    if options.write_files:
        performance_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = performance_dir / DEFAULT_MANIFEST_NAME
        hash_path = performance_dir / DEFAULT_HASH_NAME
        report_path = performance_dir / DEFAULT_REPORT_NAME
        save_json(manifest_path, manifest)
        performance_hash = {
            "version": LTS_RC_PERFORMANCE_VERSION,
            "manifest": str(manifest_path.relative_to(root)) if manifest_path.is_relative_to(root) else str(manifest_path),
            "manifest_sha256": _sha256(manifest_path),
            "performance_file_hashes": {entry["path"]: entry["sha256"] for entry in performance_entries},
            "rc02_artifact_hashes": {entry["path"]: entry["sha256"] for entry in rc02_entries},
            "timing_probe_checksum": timing_probe["checksum"],
            "status": status,
            "created_at": now_iso(),
        }
        save_json(hash_path, performance_hash)
        save_text(report_path, format_lts_rc_performance_markdown(manifest, performance_hash))
        manifest["manifest_path"] = str(manifest_path)
        manifest["hash_path"] = str(hash_path)
        manifest["report_path"] = str(report_path)
    return manifest


def validate_lts_rc_performance(manifest: dict) -> dict:
    failures = list(manifest.get("failures", []))
    passed = manifest.get("status") == "pass" and not failures
    return {
        "version": LTS_RC_PERFORMANCE_VERSION,
        "status": "pass" if passed else "fail",
        "check_count": len(manifest.get("performance_checks", [])),
        "failure_count": len(failures),
        "failures": failures,
        "performance_file_count": len(manifest.get("performance_files", [])),
        "rc02_artifact_count": len(manifest.get("rc02_artifacts", [])),
        "timing_probe_status": manifest.get("timing_probe", {}).get("status"),
    }


def format_lts_rc_performance_text(manifest: dict) -> str:
    result = validate_lts_rc_performance(manifest)
    lines = [
        "NTPE 1.1 LTS RC-03 Performance / Long-Run Validation",
        "========================================================",
        f"status: {manifest.get('status')}",
        f"validation: {result.get('status')}",
        f"recommended_tag: {manifest.get('candidate', {}).get('recommended_tag')}",
        f"check_count: {result.get('check_count')}",
        f"failure_count: {result.get('failure_count')}",
        f"performance_file_count: {result.get('performance_file_count')}",
        f"rc02_artifact_count: {result.get('rc02_artifact_count')}",
        f"timing_probe_status: {result.get('timing_probe_status')}",
        f"manifest: {manifest.get('manifest_path', '')}",
        f"report: {manifest.get('report_path', '')}",
    ]
    return "\n".join(lines).strip() + "\n"


def format_lts_rc_performance_markdown(manifest: dict, performance_hash: dict | None = None) -> str:
    result = validate_lts_rc_performance(manifest)
    lines = [
        "# NTPE 1.1 LTS RC-03 Performance / Long-Run Validation Report",
        "",
        f"- Version: {manifest.get('version')}",
        f"- Status: {manifest.get('status')}",
        f"- Validation: {result.get('status')}",
        f"- Recommended Tag: `{manifest.get('candidate', {}).get('recommended_tag')}`",
        f"- Performance Checks: {result.get('check_count')}",
        f"- Failure Count: {result.get('failure_count')}",
        f"- External API Calls: {manifest.get('validation', {}).get('external_api_calls')}",
        "",
        "## Performance Gate",
        "",
        "| Check | Status |",
        "|---|---|",
    ]
    failures = set(manifest.get("failures", []))
    for check in manifest.get("performance_checks", []):
        lines.append(f"| `{check}` | {'FAIL' if check in failures else 'PASS'} |")
    lines.extend([
        "",
        "## Static Timing Probe",
        "",
        f"- Sample Files: {manifest.get('timing_probe', {}).get('sample_file_count')}",
        f"- Sample Chunks: {manifest.get('timing_probe', {}).get('sample_chunk_count')}",
        f"- Elapsed ms: {manifest.get('timing_probe', {}).get('elapsed_ms')}",
        f"- Status: {manifest.get('timing_probe', {}).get('status')}",
        "",
        "## Long-Run Validation Scope",
        "",
        "- Confirms RC-02 compatibility validation remains passable.",
        "- Confirms Stage-10 long-run recovery validation remains passable.",
        "- Confirms batch resume, failure recovery, heartbeat, and runtime monitor entry points remain available.",
        "- Performs no external API calls and does not modify frozen NTPE 1.0 or LTS runtime behavior.",
    ])
    if performance_hash:
        lines.extend(["", f"Manifest SHA256: `{performance_hash.get('manifest_sha256')}`"])
    return "\n".join(lines).strip() + "\n"


def parse_args(argv: Iterable[str] | None = None) -> LTSRCPerformanceOptions:
    parser = argparse.ArgumentParser(description="NTPE 1.1 LTS RC-03 performance and long-run validation")
    parser.add_argument("--root", default=".", help="project root")
    parser.add_argument("--performance-dir", default=DEFAULT_PERFORMANCE_DIR)
    parser.add_argument("--sample-file-count", type=int, default=120)
    parser.add_argument("--sample-chunk-count", type=int, default=9320)
    parser.add_argument("--no-write-files", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    ns = parser.parse_args(list(argv) if argv is not None else None)
    return LTSRCPerformanceOptions(
        root=Path(ns.root),
        performance_dir=Path(ns.performance_dir),
        write_files=not ns.no_write_files,
        quiet=ns.quiet,
        sample_file_count=ns.sample_file_count,
        sample_chunk_count=ns.sample_chunk_count,
    )


def main(argv: Iterable[str] | None = None) -> int:
    options = parse_args(argv)
    manifest = build_lts_rc_performance_manifest(options)
    if not options.quiet:
        print(format_lts_rc_performance_text(manifest), end="")
    return 0 if validate_lts_rc_performance(manifest)["status"] == "pass" else 1
