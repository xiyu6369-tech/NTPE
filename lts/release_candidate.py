from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.translation_engine.utils import now_iso, save_json, save_text
from lts.runtime_freeze import DEFAULT_MANIFEST_NAME as RUNTIME_FREEZE_MANIFEST_NAME
from lts.runtime_freeze import FROZEN_RUNTIME_FILES, REQUIRED_STAGE_REPORTS

LTS_RELEASE_CANDIDATE_VERSION = "1.1-lts-rc-preparation"
DEFAULT_RC_DIR = "lts_release_candidate"
DEFAULT_MANIFEST_NAME = "LTS_Release_Candidate_Manifest_1_1.json"
DEFAULT_HASH_NAME = "LTS_Release_Candidate_Hash_1_1.json"
DEFAULT_REPORT_NAME = "LTS_Release_Candidate_Preparation_Report_1_1.md"
DEFAULT_RELEASE_NOTES_NAME = "RELEASE_NOTES_NTPE_1_1_LTS_RC.md"

REQUIRED_RC_INPUTS = [
    "LTS_Runtime_Freeze_Report_1_1.md",
    "LTS_Runtime_Freeze_Manifest_1_1.json",
    "LTS_Runtime_Freeze_Hash_1_1.json",
]

@dataclass(frozen=True)
class LTSReleaseCandidateOptions:
    root: Path = Path(".")
    rc_dir: Path = Path(DEFAULT_RC_DIR)
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


def build_lts_release_candidate_manifest(options: LTSReleaseCandidateOptions) -> dict:
    root = options.root.resolve()
    rc_dir = _resolve(root, options.rc_dir)

    runtime_entries: list[dict] = []
    missing_runtime: list[str] = []
    for rel in FROZEN_RUNTIME_FILES:
        entry = _file_entry(root, rel)
        if entry:
            runtime_entries.append(entry)
        else:
            missing_runtime.append(rel)

    stage_report_entries: list[dict] = []
    missing_stage_reports: list[str] = []
    for rel in REQUIRED_STAGE_REPORTS:
        entry = _file_entry(root, rel)
        if entry:
            stage_report_entries.append(entry)
        else:
            missing_stage_reports.append(rel)

    freeze_dir = root / "lts_runtime_freeze"
    rc_input_entries: list[dict] = []
    missing_rc_inputs: list[str] = []
    for name in REQUIRED_RC_INPUTS:
        rel = f"lts_runtime_freeze/{name}"
        entry = _file_entry(root, rel)
        if entry:
            rc_input_entries.append(entry)
        else:
            missing_rc_inputs.append(rel)

    missing = missing_runtime + missing_stage_reports + missing_rc_inputs
    status = "ready" if not missing else "incomplete"
    manifest = {
        "version": LTS_RELEASE_CANDIDATE_VERSION,
        "release_line": "NTPE 1.1 LTS",
        "stage": "Stage-12 LTS Release Candidate Preparation",
        "status": status,
        "created_at": now_iso(),
        "candidate": {
            "name": "NTPE 1.1 LTS Release Candidate",
            "recommended_tag": "v1.1.0-lts-rc-01",
            "base_runtime_freeze_manifest": f"lts_runtime_freeze/{RUNTIME_FREEZE_MANIFEST_NAME}",
            "release_type": "long_term_support_release_candidate",
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
            "stage_12_change_type": "metadata_validation_only",
        },
        "runtime_files": runtime_entries,
        "stage_reports": stage_report_entries,
        "rc_inputs": rc_input_entries,
        "missing_runtime_files": missing_runtime,
        "missing_stage_reports": missing_stage_reports,
        "missing_rc_inputs": missing_rc_inputs,
        "validation": {
            "status": "pass" if status == "ready" else "fail",
            "runtime_file_count": len(runtime_entries),
            "stage_report_count": len(stage_report_entries),
            "rc_input_count": len(rc_input_entries),
            "missing_count": len(missing),
            "selected_regression_suite": "Stable + LTS Stage-01~11 + Clean Project Tool + Stage-12",
            "expected_result": "ALL PASS",
        },
    }

    if options.write_files:
        rc_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = rc_dir / DEFAULT_MANIFEST_NAME
        hash_path = rc_dir / DEFAULT_HASH_NAME
        report_path = rc_dir / DEFAULT_REPORT_NAME
        release_notes_path = rc_dir / DEFAULT_RELEASE_NOTES_NAME
        save_json(manifest_path, manifest)
        candidate_hash = {
            "version": LTS_RELEASE_CANDIDATE_VERSION,
            "manifest": str(manifest_path.relative_to(root)) if manifest_path.is_relative_to(root) else str(manifest_path),
            "manifest_sha256": _sha256(manifest_path),
            "runtime_file_hashes": {entry["path"]: entry["sha256"] for entry in runtime_entries},
            "rc_input_hashes": {entry["path"]: entry["sha256"] for entry in rc_input_entries},
            "status": status,
            "created_at": now_iso(),
        }
        save_json(hash_path, candidate_hash)
        save_text(report_path, format_lts_release_candidate_markdown(manifest, candidate_hash))
        save_text(release_notes_path, format_lts_release_candidate_release_notes(manifest))
        manifest["manifest_path"] = str(manifest_path)
        manifest["hash_path"] = str(hash_path)
        manifest["report_path"] = str(report_path)
        manifest["release_notes_path"] = str(release_notes_path)
    return manifest


def validate_lts_release_candidate(manifest: dict) -> dict:
    missing = (
        list(manifest.get("missing_runtime_files", []))
        + list(manifest.get("missing_stage_reports", []))
        + list(manifest.get("missing_rc_inputs", []))
    )
    passed = manifest.get("status") == "ready" and not missing
    return {
        "version": LTS_RELEASE_CANDIDATE_VERSION,
        "status": "pass" if passed else "fail",
        "runtime_file_count": len(manifest.get("runtime_files", [])),
        "stage_report_count": len(manifest.get("stage_reports", [])),
        "rc_input_count": len(manifest.get("rc_inputs", [])),
        "missing_count": len(missing),
        "missing": missing,
    }


def format_lts_release_candidate_text(manifest: dict) -> str:
    result = validate_lts_release_candidate(manifest)
    lines = [
        "NTPE 1.1 LTS Release Candidate Preparation",
        "=============================================",
        f"status: {manifest.get('status')}",
        f"validation: {result.get('status')}",
        f"recommended_tag: {manifest.get('candidate', {}).get('recommended_tag')}",
        f"runtime_file_count: {result.get('runtime_file_count')}",
        f"stage_report_count: {result.get('stage_report_count')}",
        f"rc_input_count: {result.get('rc_input_count')}",
        f"missing_count: {result.get('missing_count')}",
        f"manifest: {manifest.get('manifest_path', '')}",
        f"report: {manifest.get('report_path', '')}",
        f"release_notes: {manifest.get('release_notes_path', '')}",
    ]
    return "\n".join(lines).strip() + "\n"


def format_lts_release_candidate_markdown(manifest: dict, candidate_hash: dict | None = None) -> str:
    result = validate_lts_release_candidate(manifest)
    lines = [
        "# NTPE 1.1 LTS Stage-12 Release Candidate Preparation Report",
        "",
        f"- Version: {manifest.get('version')}",
        f"- Status: {manifest.get('status')}",
        f"- Validation: {result.get('status')}",
        f"- Recommended Tag: `{manifest.get('candidate', {}).get('recommended_tag')}`",
        f"- Runtime Files: {result.get('runtime_file_count')}",
        f"- Stage Reports: {result.get('stage_report_count')}",
        f"- RC Inputs: {result.get('rc_input_count')}",
        f"- Missing Count: {result.get('missing_count')}",
        "",
        "## Scope",
        "",
        "- Converts the frozen LTS runtime into a release-candidate package.",
        "- Adds validation metadata, hash manifest, and release notes draft.",
        "- Does not alter Foundation v1.0, CLI, SDK, Runtime API, REST API, Web UI, or frozen LTS runtime behavior.",
        "",
        "## Validation Gate",
        "",
        "| Item | Status |",
        "|---|---|",
        f"| Frozen runtime files present | {'PASS' if not manifest.get('missing_runtime_files') else 'FAIL'} |",
        f"| LTS stage reports present | {'PASS' if not manifest.get('missing_stage_reports') else 'FAIL'} |",
        f"| Stage-11 runtime freeze inputs present | {'PASS' if not manifest.get('missing_rc_inputs') else 'FAIL'} |",
        f"| Candidate status | {manifest.get('status').upper()} |",
        "",
        "## Compatibility Policy",
        "",
    ]
    for key, value in manifest.get("compatibility_policy", {}).items():
        lines.append(f"- {key}: {value}")
    if candidate_hash:
        lines.extend(["", f"Manifest SHA256: `{candidate_hash.get('manifest_sha256')}`"])
    return "\n".join(lines).strip() + "\n"


def format_lts_release_candidate_release_notes(manifest: dict) -> str:
    lines = [
        "# NTPE 1.1 LTS Release Candidate Notes",
        "",
        "## Candidate",
        "",
        f"- Name: {manifest.get('candidate', {}).get('name')}",
        f"- Recommended Tag: `{manifest.get('candidate', {}).get('recommended_tag')}`",
        f"- Status: {manifest.get('status')}",
        "",
        "## Included LTS Capabilities",
        "",
        "- TXT novel translation entry",
        "- Resume / retry hardening",
        "- Glossary and character memory strengthening",
        "- Translation QA and Korean residue checks",
        "- Taiwan Traditional Chinese output normalization",
        "- Batch folder translation",
        "- Batch progress and summary reports",
        "- Batch failure recovery / continue mode",
        "- Batch runtime monitor",
        "- Long-run stability and auto recovery",
        "- LTS runtime freeze validation",
        "",
        "## Release Gate",
        "",
        "This candidate is ready only when Stage-12 validation is PASS and the full regression suite reports ALL PASS.",
    ]
    return "\n".join(lines).strip() + "\n"


def parse_args(argv: Iterable[str] | None = None) -> LTSReleaseCandidateOptions:
    parser = argparse.ArgumentParser(description="NTPE 1.1 LTS Stage-12 release candidate preparation")
    parser.add_argument("--root", default=".", help="project root")
    parser.add_argument("--rc-dir", default=DEFAULT_RC_DIR)
    parser.add_argument("--no-write-files", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    ns = parser.parse_args(list(argv) if argv is not None else None)
    return LTSReleaseCandidateOptions(
        root=Path(ns.root),
        rc_dir=Path(ns.rc_dir),
        write_files=not ns.no_write_files,
        quiet=ns.quiet,
    )


def main(argv: Iterable[str] | None = None) -> int:
    options = parse_args(argv)
    manifest = build_lts_release_candidate_manifest(options)
    if not options.quiet:
        print(format_lts_release_candidate_text(manifest), end="")
    return 0 if validate_lts_release_candidate(manifest)["status"] == "pass" else 1
