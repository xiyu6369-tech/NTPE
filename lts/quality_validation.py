from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.translation_engine.utils import now_iso, save_json, save_text
from lts.performance_validation import (
    LTS_RC_PERFORMANCE_VERSION,
    LTSRCPerformanceOptions,
    build_lts_rc_performance_manifest,
    validate_lts_rc_performance,
)
from lts.txt_translation_runtime import (
    TxtTranslationOptions,
    analyze_translation_quality,
    count_korean_characters,
    detect_repeated_lines,
    format_translation_output,
)

LTS_RC_QUALITY_VERSION = "1.1-lts-rc-04"
DEFAULT_QUALITY_DIR = "lts_rc_quality"
DEFAULT_MANIFEST_NAME = "LTS_RC_04_Translation_Quality_QA_Validation_Manifest_1_1.json"
DEFAULT_HASH_NAME = "LTS_RC_04_Translation_Quality_QA_Validation_Hash_1_1.json"
DEFAULT_REPORT_NAME = "LTS_RC_04_Translation_Quality_QA_Validation_Report_1_1.md"

REQUIRED_RC03_ARTIFACTS = [
    "lts_rc_performance/LTS_RC_03_Performance_Long_Run_Validation_Manifest_1_1.json",
    "lts_rc_performance/LTS_RC_03_Performance_Long_Run_Validation_Hash_1_1.json",
    "lts_rc_performance/LTS_RC_03_Performance_Long_Run_Validation_Report_1_1.md",
]

QUALITY_FILES = [
    "ntpe_translate_txt.py",
    "ntpe_translate_batch.py",
    "lts/txt_translation_runtime.py",
    "tests/lts_stage_04/test_translation_qa.py",
    "tests/lts_stage_05/test_output_formatter.py",
]

QUALITY_CHECKS = [
    "rc03_performance_validation_passes",
    "rc03_artifact_chain_present",
    "quality_files_present",
    "korean_residue_detector_passes",
    "length_ratio_gate_passes",
    "repeated_line_detector_passes",
    "formatter_normalization_gate_passes",
    "qa_failure_case_detected",
    "qa_clean_case_passes",
]


@dataclass(frozen=True)
class LTSRCQualityOptions:
    root: Path = Path(".")
    quality_dir: Path = Path(DEFAULT_QUALITY_DIR)
    write_files: bool = True
    quiet: bool = False
    max_korean_chars: int = 3
    min_length_ratio: float = 0.25


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


def _quality_probe(options: LTSRCQualityOptions) -> dict:
    qa_options = TxtTranslationOptions(
        input_path=Path("quality_probe.txt"),
        output_dir=Path("output"),
        max_korean_chars=0,
        min_length_ratio=options.min_length_ratio,
    )
    source = "정태의는 창밖을 바라보았다. 그리고 오래 침묵했다."
    failed_translation = "정태의\n"
    clean_translation = "鄭泰義望向窗外，然後沉默了很久。"
    formatted_sample = format_translation_output("他说, \"这里没有问题!\"", qa_options)
    failed_report = analyze_translation_quality(source, failed_translation, qa_options)
    clean_report = analyze_translation_quality(source, clean_translation, qa_options)
    repeated = detect_repeated_lines("同一句話。\n同一句話。\n同一句話。\n", max_repeated_lines=2)

    return {
        "mode": "static_quality_probe_no_external_api",
        "korean_residue_detector_passes": count_korean_characters("정태의") >= 3 and count_korean_characters(clean_translation) == 0,
        "length_ratio_gate_passes": any(issue.get("code") == "LENGTH_RATIO_TOO_LOW" for issue in failed_report.get("issues", [])),
        "repeated_line_detector_passes": repeated == ["同一句話。"],
        "formatter_normalization_gate_passes": "說" in formatted_sample and "這裡" in formatted_sample and "！" in formatted_sample,
        "qa_failure_case_detected": not failed_report.get("passed") and any(issue.get("code") == "KOREAN_RESIDUE" for issue in failed_report.get("issues", [])),
        "qa_clean_case_passes": clean_report.get("passed") is True,
        "failed_case_metrics": failed_report.get("metrics", {}),
        "clean_case_metrics": clean_report.get("metrics", {}),
        "status": "pass" if (
            count_korean_characters("정태의") >= 3
            and count_korean_characters(clean_translation) == 0
            and any(issue.get("code") == "LENGTH_RATIO_TOO_LOW" for issue in failed_report.get("issues", []))
            and repeated == ["同一句話。"]
            and "說" in formatted_sample
            and "這裡" in formatted_sample
            and "！" in formatted_sample
            and not failed_report.get("passed")
            and clean_report.get("passed") is True
        ) else "fail",
    }


def build_lts_rc_quality_manifest(options: LTSRCQualityOptions) -> dict:
    root = options.root.resolve()
    quality_dir = _resolve(root, options.quality_dir)

    performance_manifest = build_lts_rc_performance_manifest(
        LTSRCPerformanceOptions(root=root, write_files=False)
    )
    performance_result = validate_lts_rc_performance(performance_manifest)
    rc03_entries, missing_rc03 = _collect_entries(root, REQUIRED_RC03_ARTIFACTS)
    quality_entries, missing_quality_files = _collect_entries(root, QUALITY_FILES)
    quality_probe = _quality_probe(options)

    failures: list[str] = []
    if performance_result["status"] != "pass":
        failures.append("rc03_performance_validation_passes")
    if missing_rc03:
        failures.append("rc03_artifact_chain_present")
    if missing_quality_files:
        failures.append("quality_files_present")
    for check in QUALITY_CHECKS[3:]:
        if not quality_probe.get(check):
            failures.append(check)

    status = "pass" if not failures else "fail"
    manifest = {
        "version": LTS_RC_QUALITY_VERSION,
        "release_line": "NTPE 1.1 LTS",
        "stage": "RC-04 Translation Quality / QA Validation",
        "status": status,
        "created_at": now_iso(),
        "candidate": {
            "source_stage": "RC-03 Performance / Long-Run Validation",
            "source_version": LTS_RC_PERFORMANCE_VERSION,
            "recommended_tag": "v1.1.0-lts-rc-04-quality",
        },
        "quality_checks": QUALITY_CHECKS,
        "performance_validation": performance_result,
        "quality_probe": quality_probe,
        "rc03_artifacts": rc03_entries,
        "quality_files": quality_entries,
        "missing_rc03_artifacts": missing_rc03,
        "missing_quality_files": missing_quality_files,
        "failures": failures,
        "validation": {
            "status": status,
            "check_count": len(QUALITY_CHECKS),
            "failure_count": len(failures),
            "quality_file_count": len(quality_entries),
            "rc03_artifact_count": len(rc03_entries),
            "selected_regression_suite": "Stable + LTS Stage-01~12 + RC-01~04",
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
            "rc_04_change_type": "translation_quality_validation_metadata_only",
        },
    }

    if options.write_files:
        quality_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = quality_dir / DEFAULT_MANIFEST_NAME
        hash_path = quality_dir / DEFAULT_HASH_NAME
        report_path = quality_dir / DEFAULT_REPORT_NAME
        save_json(manifest_path, manifest)
        quality_hash = {
            "version": LTS_RC_QUALITY_VERSION,
            "manifest": str(manifest_path.relative_to(root)) if manifest_path.is_relative_to(root) else str(manifest_path),
            "manifest_sha256": _sha256(manifest_path),
            "quality_file_hashes": {entry["path"]: entry["sha256"] for entry in quality_entries},
            "rc03_artifact_hashes": {entry["path"]: entry["sha256"] for entry in rc03_entries},
            "quality_probe_status": quality_probe.get("status"),
            "status": status,
            "created_at": now_iso(),
        }
        save_json(hash_path, quality_hash)
        save_text(report_path, format_lts_rc_quality_markdown(manifest, quality_hash))
        manifest["manifest_path"] = str(manifest_path)
        manifest["hash_path"] = str(hash_path)
        manifest["report_path"] = str(report_path)
    return manifest


def validate_lts_rc_quality(manifest: dict) -> dict:
    failures = list(manifest.get("failures", []))
    passed = manifest.get("status") == "pass" and not failures
    return {
        "version": LTS_RC_QUALITY_VERSION,
        "status": "pass" if passed else "fail",
        "check_count": len(manifest.get("quality_checks", [])),
        "failure_count": len(failures),
        "failures": failures,
        "quality_file_count": len(manifest.get("quality_files", [])),
        "rc03_artifact_count": len(manifest.get("rc03_artifacts", [])),
        "quality_probe_status": manifest.get("quality_probe", {}).get("status"),
    }


def format_lts_rc_quality_text(manifest: dict) -> str:
    result = validate_lts_rc_quality(manifest)
    lines = [
        "NTPE 1.1 LTS RC-04 Translation Quality / QA Validation",
        "========================================================",
        f"status: {manifest.get('status')}",
        f"validation: {result.get('status')}",
        f"recommended_tag: {manifest.get('candidate', {}).get('recommended_tag')}",
        f"check_count: {result.get('check_count')}",
        f"failure_count: {result.get('failure_count')}",
        f"quality_file_count: {result.get('quality_file_count')}",
        f"rc03_artifact_count: {result.get('rc03_artifact_count')}",
        f"quality_probe_status: {result.get('quality_probe_status')}",
        f"manifest: {manifest.get('manifest_path', '')}",
        f"report: {manifest.get('report_path', '')}",
    ]
    return "\n".join(lines).strip() + "\n"


def format_lts_rc_quality_markdown(manifest: dict, quality_hash: dict | None = None) -> str:
    result = validate_lts_rc_quality(manifest)
    failures = set(manifest.get("failures", []))
    lines = [
        "# NTPE 1.1 LTS RC-04 Translation Quality / QA Validation Report",
        "",
        f"- Version: {manifest.get('version')}",
        f"- Status: {manifest.get('status')}",
        f"- Validation: {result.get('status')}",
        f"- Recommended Tag: `{manifest.get('candidate', {}).get('recommended_tag')}`",
        f"- Quality Checks: {result.get('check_count')}",
        f"- Failure Count: {result.get('failure_count')}",
        f"- External API Calls: {manifest.get('validation', {}).get('external_api_calls')}",
        "",
        "## QA Gate",
        "",
        "| Check | Status |",
        "|---|---|",
    ]
    for check in manifest.get("quality_checks", []):
        lines.append(f"| `{check}` | {'FAIL' if check in failures else 'PASS'} |")
    probe = manifest.get("quality_probe", {})
    lines.extend([
        "",
        "## Static Quality Probe",
        "",
        f"- Mode: {probe.get('mode')}",
        f"- Status: {probe.get('status')}",
        f"- Korean Residue Detector: {probe.get('korean_residue_detector_passes')}",
        f"- Length Ratio Gate: {probe.get('length_ratio_gate_passes')}",
        f"- Repeated Line Detector: {probe.get('repeated_line_detector_passes')}",
        f"- Formatter Normalization: {probe.get('formatter_normalization_gate_passes')}",
        "",
        "## Validation Scope",
        "",
        "- Confirms RC-03 performance validation remains passable.",
        "- Confirms Korean residue, short-output, repeated-line, and formatting QA gates remain active.",
        "- Performs no external API calls and does not modify frozen NTPE 1.0 or LTS runtime behavior.",
    ])
    if quality_hash:
        lines.extend(["", f"Manifest SHA256: `{quality_hash.get('manifest_sha256')}`"])
    return "\n".join(lines).strip() + "\n"


def parse_args(argv: Iterable[str] | None = None) -> LTSRCQualityOptions:
    parser = argparse.ArgumentParser(description="NTPE 1.1 LTS RC-04 translation quality and QA validation")
    parser.add_argument("--root", default=".", help="project root")
    parser.add_argument("--quality-dir", default=DEFAULT_QUALITY_DIR)
    parser.add_argument("--max-korean-chars", type=int, default=3)
    parser.add_argument("--min-length-ratio", type=float, default=0.25)
    parser.add_argument("--no-write-files", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    ns = parser.parse_args(list(argv) if argv is not None else None)
    return LTSRCQualityOptions(
        root=Path(ns.root),
        quality_dir=Path(ns.quality_dir),
        write_files=not ns.no_write_files,
        quiet=ns.quiet,
        max_korean_chars=ns.max_korean_chars,
        min_length_ratio=ns.min_length_ratio,
    )


def main(argv: Iterable[str] | None = None) -> int:
    options = parse_args(argv)
    manifest = build_lts_rc_quality_manifest(options)
    if not options.quiet:
        print(format_lts_rc_quality_text(manifest), end="")
    return 0 if validate_lts_rc_quality(manifest)["status"] == "pass" else 1
