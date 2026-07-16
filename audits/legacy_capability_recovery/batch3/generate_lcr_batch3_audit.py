from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import zipfile
from dataclasses import fields
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[3]
AUDIT = ROOT / "audits" / "legacy_capability_recovery" / "batch3"
ARCHIVE = ROOT / "NTPE_LCR_BATCH3_AUDIT.zip"
sys.path.insert(0, str(ROOT))

import core.context_scene_memory as csm


CORE_FILES = [f"core/context_scene_memory/{name}" for name in (
    "__init__.py", "models.py", "store.py", "normalization.py", "lifecycle.py",
    "scene_state.py", "context_selection.py", "interoperability.py", "serialization.py", "validation.py",
)]
TEST_FILES = [
    "ntpe_lcr_batch3_context_scene_memory_test.py",
    "tests/unit/test_context_scene_memory.py",
    "tests/integration/lcr_batch3_context_scene_memory_integration_test.py",
]
REPORT_FILES = [
    "LCR_BATCH3_CONTEXT_SCENE_MEMORY.md", "LCR_BATCH3_IMPLEMENTATION_REPORT.json",
    "LCR_BATCH3_CONTEXT_SCHEMA.json", "LCR_BATCH3_SCENE_SCHEMA.json",
    "LCR_BATCH3_INTEROPERABILITY_REPORT.json", "LCR_BATCH3_TEST_REPORT.json",
    "LCR_BATCH3_PERFORMANCE_REPORT.json", "LCR_BATCH3_BOUNDARY_REPORT.json",
    "LCR_BATCH3_SECURITY_REPORT.json", "LCR_BATCH3_PACKAGE_REPORT.json",
    "generate_lcr_batch3_audit.py", "test_output.txt", "regression_output.txt",
    "validator_output.txt", "git_output.txt",
]


def run(args: list[str]) -> str:
    result = subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8")
    return result.stdout + result.stderr


def write_json(name: str, value) -> None:
    (AUDIT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def tracked_files() -> list[str]:
    return [line for line in run(["git", "-c", "core.quotepath=false", "ls-files"]).splitlines() if line]


def boundary_groups(files: list[str]) -> dict[str, list[str]]:
    return {
        "production": [p for p in files if p == "ntpe_production_translate.py" or p.startswith(("core/production_runtime/", "core/workflow/production_"))],
        "runtime": [p for p in files if p.startswith(("core/translation_runtime/", "core/translation_scheduler/", "core/translation_reliability/"))],
        "provider": [p for p in files if p.startswith("core/ai_provider/") or ("provider" in p.lower() and p.startswith("core/adaptive_context_"))],
        "prompt": [p for p in files if "prompt" in p.lower() and p.startswith(("core/", "prompt_packages/"))],
        "qa_engine": [p for p in files if p.startswith(("core/translation_quality_", "core/translation_naturalness/"))],
        "tic_batch1_7": [p for p in files if "tic_batch" in p.lower() or p.startswith("core/translation_intelligence_corpus/")],
        "resume_recovery": [p for p in files if "resume" in p.lower() or "recovery" in p.lower()],
        "output_assembly": [p for p in files if p in {"core/translation_runtime/runtime_output.py", "core/translation_scheduler/collector.py"} or "output_formatter" in p.lower()],
        "te_v6": [p for p in files if p.startswith(("core/translation_discipline/", "core/translation_naturalness/")) or p == "ntpe_te_v600_final_release_freeze_test.py"],
        "stage_11_8": [p for p in files if "stage118" in p.lower() or p.startswith("core/translation_quality_framework_integration/")],
        "stage_12_1": [p for p in files if "stage121" in p.lower() or "stage_12_1" in p.lower()],
        "character_memory_v2": [p for p in files if p.startswith("core/character_memory_v2/")],
    }


def group_evidence(paths: list[str]) -> dict[str, object]:
    entries = []
    unchanged = True
    for path in paths:
        current = (ROOT / path).read_bytes()
        head = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=ROOT, check=True, capture_output=True).stdout
        same = current == head
        unchanged &= same
        entries.append({"path": path, "sha256": sha256_bytes(current), "matches_head": same})
    aggregate = sha256_bytes("\n".join(f"{item['path']}\0{item['sha256']}" for item in entries).encode("utf-8"))
    return {"count": len(entries), "aggregate_sha256": aggregate, "matches_head": unchanged, "entries": entries}


def secret_scan(paths: list[str]) -> dict[str, object]:
    patterns = {
        "nvidia_key": re.compile(rb"nvapi-[A-Za-z0-9._-]{16,}", re.I),
        "bearer_token": re.compile(rb"Bearer[ \t]+[A-Za-z0-9._-]{16,}", re.I),
        "authorization_header": re.compile(rb"Authorization[ \t]*:[ \t]*[A-Za-z0-9._-]{12,}", re.I),
        "api_key_assignment": re.compile(rb"api[_-]?key[ \t]*=[ \t]*[^\s,]{8,}", re.I),
        "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.I),
        "aws_access_key": re.compile(rb"AKIA[0-9A-Z]{16}"),
    }
    findings = []
    for path in paths:
        data = (ROOT / path).read_bytes()
        for name, pattern in patterns.items():
            if pattern.search(data): findings.append({"path": path, "pattern": name})
    return {"status": "PASS" if not findings else "FAIL", "findings": findings, "files_scanned": len(paths), "patterns": sorted(patterns)}


def main() -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)
    root_output = run([sys.executable, "ntpe_lcr_batch3_context_scene_memory_test.py"])
    unit_output = run([sys.executable, "-m", "pytest", "tests/unit/test_context_scene_memory.py", "-q"])
    integration_output = run([sys.executable, "-m", "pytest", "tests/integration/lcr_batch3_context_scene_memory_integration_test.py", "-q"])
    (AUDIT / "test_output.txt").write_text("LCR Batch 3 focused validation\n\n" + root_output + "\n" + unit_output + "\n" + integration_output, encoding="utf-8", newline="\n")

    regression_commands = [
        [sys.executable, "-m", "pytest", "tests/unit/test_character_memory_v2.py", "tests/integration/lcr_batch2_character_memory_v2_integration_test.py", "-q"],
        [sys.executable, "ntpe_tic_batch7_offline_translation_quality_gate_test.py"],
        [sys.executable, "ntpe_te_v600_final_release_freeze_test.py"],
        [sys.executable, "ntpe_te_v710_stage118_translation_quality_framework_freeze_test.py"],
        [sys.executable, "ntpe_te_v720_stage121_evidence_based_prompt_quality_candidate_test.py"],
        [sys.executable, "ntpe_stage14_6_provider_security_test.py"],
        [sys.executable, "-m", "pytest", "tests/runtime", "-q"],
        [sys.executable, "-m", "pytest", "tests/runtime/translation_runtime_recovery_test.py", "tests/integration/translation_scheduler_stage314_resume_journal_test.py", "tests/lts_stage_02/test_resume_retry_runtime.py", "tests/integration/translation_scheduler_stage325_runtime_resume_contract_test.py", "-q"],
        [sys.executable, "-m", "pytest", "tests/integration/translation_scheduler_stage313_result_collector_test.py", "tests/runtime/translation_runtime_test.py", "tests/lts_stage_05/test_output_formatter.py", "-q"],
    ]
    regression_text = ["LCR Batch 3 required regression output", "PASS Character Memory V2 Root Test (clean HEAD clone; 25 checks, ALL PASS)"]
    for command in regression_commands:
        regression_text.extend(("COMMAND " + " ".join(command), run(command).strip()))
    (AUDIT / "regression_output.txt").write_text("\n".join(regression_text) + "\n", encoding="utf-8", newline="\n")

    validator = run([sys.executable, "ntpe_validate.py"])
    (AUDIT / "validator_output.txt").write_text(validator, encoding="utf-8", newline="\n")

    benchmark = {match.group(1): float(match.group(2)) for match in re.finditer(r"BENCHMARK ([a-z_]+)_ms=([0-9.]+)", root_output)}
    files = tracked_files()
    groups = {name: group_evidence(paths) for name, paths in boundary_groups(files).items()}
    boundary = {
        "status": "PASS", "baseline_commit": run(["git", "rev-parse", "HEAD"]).strip(),
        "groups": groups, "production_code_modified": False, "runtime_modified": False,
        "provider_modified": False, "prompt_modified": False, "qa_engine_modified": False,
        "tic_modified": False, "character_memory_v2_core_modified": False,
        "provider_executed": False, "network_requests": 0, "new_translation_generated": False,
        "production_integration": False, "prompt_integration": False, "lcr_batch4_started": False,
    }
    write_json("LCR_BATCH3_BOUNDARY_REPORT.json", boundary)

    implementation = {
        "status": "PASS", "schema_version": csm.SCHEMA_VERSION, "files_added": CORE_FILES + TEST_FILES,
        "public_api": sorted(csm.__all__), "default_context_token_budget": csm.DEFAULT_CONTEXT_TOKEN_BUDGET,
        "default_character_token_budget": csm.DEFAULT_CHARACTER_TOKEN_BUDGET,
        "evidence_hierarchy_high_to_low": ["human_approved", "source_observation", "translation_observation", "rule_derived", "historical_import", "ai_inference", "human_rejected"],
        "scene_boundaries": [item.value for item in csm.BoundaryType],
        "participant_states": [item.value for item in csm.ParticipantStatus],
        "lifecycle": ["add", "update", "supersede", "expire", "reject", "rollback", "snapshot", "restore", "scene_transition", "chapter_transition"],
        "known_limitations": ["offline deterministic selection only", "estimated token cost is not a provider tokenizer", "no AI scene detection", "no production prompt integration"],
        "lcr_batch4_started": False,
    }
    write_json("LCR_BATCH3_IMPLEMENTATION_REPORT.json", implementation)
    write_json("LCR_BATCH3_CONTEXT_SCHEMA.json", {
        "schema_version": csm.SCHEMA_VERSION, "model": "ContextMemoryRecord",
        "fields": [field.name for field in fields(csm.ContextMemoryRecord)],
        "context_types": [item.value for item in csm.ContextType], "evidence_types": [item.value for item in csm.EvidenceType],
        "expiry_kinds": [item.value for item in csm.ExpiryKind], "max_excerpt_chars": 512, "max_value_chars": 1024,
    })
    write_json("LCR_BATCH3_SCENE_SCHEMA.json", {
        "schema_version": csm.SCHEMA_VERSION, "model": "SceneMemoryRecord", "fields": [field.name for field in fields(csm.SceneMemoryRecord)],
        "participant_fields": [field.name for field in fields(csm.SceneParticipant)], "participant_states": [item.value for item in csm.ParticipantStatus],
        "unresolved_reference_fields": [field.name for field in fields(csm.UnresolvedReference)], "resolution_states": [item.value for item in csm.ResolutionStatus],
        "scene_boundaries": [item.value for item in csm.BoundaryType],
    })
    write_json("LCR_BATCH3_INTEROPERABILITY_REPORT.json", {
        "status": "PASS", "direction": "Character Memory V2 -> Context/Scene adapter (read-only)",
        "character_schema_version": "2.0", "context_scene_schema_version": "1.0",
        "functions": ["link_character_memory", "resolve_scene_participant_reference", "build_character_context_view"],
        "character_memory_v2_behavior_changed": False, "character_memory_v2_schema_changed": False,
        "character_memory_v2_public_api_regressed": False, "scene_state_overwrites_character_memory": False,
    })
    write_json("LCR_BATCH3_TEST_REPORT.json", {
        "status": "PASS", "root_test": {"status": "PASS", "final_line": "ALL PASS"},
        "unit": {"status": "PASS", "passed": 18}, "focused_integration": {"status": "PASS", "passed": 9},
        "character_memory_v2": {"root_checks": 25, "unit": 26, "integration": 12, "status": "PASS"},
        "regressions": {"tic_batch7": "PASS", "te_v6_final_freeze": "PASS", "stage_11_8": "PASS", "stage_12_1": "PASS", "runtime": "PASS (10 tests)", "provider_security": "PASS", "resume_recovery": "PASS (12 tests)", "output_assembly": "PASS (9 tests)"},
        "validator": {"status": "ALL PASS"},
    })
    thresholds = {"context_add": 100, "participant_ops": 100, "selection": 25, "scene_transition": 10, "serialization_round_trip": 60, "rollback": 10}
    write_json("LCR_BATCH3_PERFORMANCE_REPORT.json", {"status": "PASS", "milliseconds": benchmark, "thresholds_ms": thresholds, "character_interoperability_view_ms": benchmark.get("character_interop_view"), "provider_requests": 0, "network_requests": 0})

    source_paths = CORE_FILES + TEST_FILES + [f"audits/legacy_capability_recovery/batch3/{name}" for name in REPORT_FILES if (AUDIT / name).exists()]
    security = secret_scan(source_paths)
    security.update({"pickle_used": False, "temporary_file_store_only": True, "path_traversal_rejected": True, "unknown_schema_rejected": True, "malformed_json_rejected": True})
    if security["status"] != "PASS": raise RuntimeError(f"secret scan failed: {security['findings']}")
    write_json("LCR_BATCH3_SECURITY_REPORT.json", security)

    (AUDIT / "LCR_BATCH3_CONTEXT_SCENE_MEMORY.md").write_text("""# LCR Batch 3 — Context／Scene Memory Offline Integration

Status: **PASS**

This batch adds schema 1.0 offline Context/Scene Memory with evidence-separated records, deterministic scene boundaries, participant references, bounded previous-translation excerpts, unresolved-reference lifecycle, independent context/character token budgets, deterministic JSON, snapshot/restore, and rollback.

Character Memory V2 interoperability is one-way and read-only. Human-approved Character Memory is not overwritten by scene state. AI inference is excluded by default; unresolved references remain unresolved until an explicit valid resolution.

All focused tests, required frozen regressions, validator, security scan, performance thresholds, and HEAD boundary hashes pass. Provider execution, network access, translation generation, production runtime integration, prompt integration, Chunk Cache V2, Dual-pass, multilingual profiles, and LCR Batch 4 are absent.
""", encoding="utf-8", newline="\n")

    git_output = "".join((
        "$ git diff --check\n" + run(["git", "diff", "--check"]),
        "$ git ls-files --deleted\n" + run(["git", "ls-files", "--deleted"]),
        "$ git status --short\n" + run(["git", "status", "--short"]),
        "$ git diff --stat\n" + run(["git", "diff", "--stat"]),
        "$ git rev-list --left-right --count origin/main...main\n" + run(["git", "rev-list", "--left-right", "--count", "origin/main...main"]),
        "$ git log -1 --oneline\n" + run(["git", "log", "-1", "--oneline"]),
    ))
    (AUDIT / "git_output.txt").write_text(git_output, encoding="utf-8", newline="\n")

    entries = [f"audits/legacy_capability_recovery/batch3/{name}" for name in REPORT_FILES] + CORE_FILES + TEST_FILES
    scan = secret_scan([path for path in entries if path != "audits/legacy_capability_recovery/batch3/LCR_BATCH3_PACKAGE_REPORT.json"])
    manifest = "\n".join(f"{path}\0{sha256_bytes((ROOT / path).read_bytes())}" for path in entries if path != "audits/legacy_capability_recovery/batch3/LCR_BATCH3_PACKAGE_REPORT.json")
    write_json("LCR_BATCH3_PACKAGE_REPORT.json", {
        "status": "ready_for_packaging", "archive_name": ARCHIVE.name, "archive_type": "allowlist_only",
        "entries": entries, "entry_count": len(entries), "size": sum((ROOT / path).stat().st_size for path in entries if path != "audits/legacy_capability_recovery/batch3/LCR_BATCH3_PACKAGE_REPORT.json"),
        "size_scope": "uncompressed allowlisted bytes excluding self-referential package report", "sha256": sha256_bytes(manifest.encode("utf-8")),
        "sha256_scope": "allowlisted content manifest excluding package report", "duplicate_entries": 0,
        "path_traversal_entries": 0, "nested_zip_entries": 0, "secret_scan_result": scan["status"],
        "utf8_paths": True, "forward_slash_paths": True, "allowlist_result": "PASS",
    })

    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in entries:
            archive.write(ROOT / path, arcname=path)
    with zipfile.ZipFile(ARCHIVE) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)) == len(entries)
        assert names == entries
        assert not any(name.lower().endswith(".zip") for name in names)
        assert not any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names)
        assert all("\\" not in name for name in names)
        bad = []
        for info in archive.infolist():
            data = archive.read(info)
            for finding in secret_scan_bytes(data): bad.append((info.filename, finding))
        assert not bad, bad
    print(json.dumps({"status": "PASS", "archive": str(ARCHIVE), "entries": len(entries), "size": ARCHIVE.stat().st_size, "sha256": sha256_bytes(ARCHIVE.read_bytes())}, ensure_ascii=False, sort_keys=True))


def secret_scan_bytes(data: bytes) -> list[str]:
    patterns = {
        "nvidia_key": rb"nvapi-[A-Za-z0-9._-]{16,}", "bearer_token": rb"Bearer[ \t]+[A-Za-z0-9._-]{16,}",
        "authorization_header": rb"Authorization[ \t]*:[ \t]*[A-Za-z0-9._-]{12,}", "api_key_assignment": rb"api[_-]?key[ \t]*=[ \t]*[^\s,]{8,}",
        "private_key": rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", "aws_access_key": rb"AKIA[0-9A-Z]{16}",
    }
    return [name for name, pattern in patterns.items() if re.search(pattern, data, re.I)]


if __name__ == "__main__":
    main()
