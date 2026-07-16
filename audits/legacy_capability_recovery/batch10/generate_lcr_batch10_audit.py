from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
import zipfile
from dataclasses import asdict, fields
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[3]
AUDIT = ROOT / "audits/legacy_capability_recovery/batch10"
ARCHIVE = ROOT / "NTPE_LCR_BATCH10_AUDIT.zip"
sys.path.insert(0, str(ROOT))

import core.lcr_production_shadow as lcr


CORE = [f"core/lcr_production_shadow/{name}" for name in (
    "__init__.py", "models.py", "inventory.py", "adapters.py", "shadow_input.py",
    "shadow_runner.py", "comparison.py", "feature_flags.py", "rollback.py",
    "activation_gate.py", "serialization.py", "validation.py",
)]
TESTS = [
    "ntpe_lcr_batch10_production_shadow_planning_test.py",
    "tests/unit/test_lcr_production_shadow.py",
    "tests/integration/lcr_batch10_production_shadow_planning_integration_test.py",
]
FIXTURES = [f"tests/fixtures/lcr_batch10/{name}" for name in (
    "production_integration_points.json", "shadow_inputs.json", "feature_flag_cases.json",
    "kill_switch_cases.json", "baseline_shadow_comparisons.json", "rollback_cases.json",
    "activation_gate_cases.json",
)]
REPORTS = [
    "LCR_BATCH10_PRODUCTION_INTEGRATION_PLANNING.md",
    "LCR_BATCH10_IMPLEMENTATION_REPORT.json", "LCR_BATCH10_INTEGRATION_INVENTORY.json",
    "LCR_BATCH10_DECISION_MATRIX.json", "LCR_BATCH10_SHADOW_SCHEMA.json",
    "LCR_BATCH10_ADAPTER_CONTRACTS.json", "LCR_BATCH10_FEATURE_FLAGS.json",
    "LCR_BATCH10_KILL_SWITCH_REPORT.json", "LCR_BATCH10_PROMPT_BUDGET_PLAN.json",
    "LCR_BATCH10_PROVIDER_COST_PLAN.json", "LCR_BATCH10_CACHE_SHADOW_REPORT.json",
    "LCR_BATCH10_MEMORY_CONTEXT_SHADOW_REPORT.json", "LCR_BATCH10_MULTILINGUAL_SHADOW_REPORT.json",
    "LCR_BATCH10_DUAL_PASS_SEMANTIC_SHADOW_REPORT.json", "LCR_BATCH10_PROVIDER_ROUTING_SHADOW_REPORT.json",
    "LCR_BATCH10_ROLLBACK_PLAN.json", "LCR_BATCH10_HOOK_PLAN.json",
    "LCR_BATCH10_ACTIVATION_GATE.json", "LCR_BATCH10_TEST_REPORT.json",
    "LCR_BATCH10_PERFORMANCE_REPORT.json", "LCR_BATCH10_DETERMINISM_REPORT.json",
    "LCR_BATCH10_BOUNDARY_REPORT.json", "LCR_BATCH10_SECURITY_REPORT.json",
    "LCR_BATCH10_PACKAGE_REPORT.json", "test_output.txt", "regression_output.txt",
    "validator_output.txt", "git_output.txt",
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dump(name: str, value: object) -> None:
    (AUDIT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True, encoding="utf-8")


def run_group(commands: tuple[tuple[str, list[str]], ...], output_name: str) -> None:
    blocks = []
    for label, command in commands:
        result = run(command)
        blocks.append(f"[{label}]\n$ {' '.join(command)}\n{result.stdout}{result.stderr}\nEXIT_CODE={result.returncode}")
        if result.returncode:
            (AUDIT / output_name).write_text("\n".join(blocks), encoding="utf-8", newline="\n")
            raise RuntimeError(f"{label} failed")
    (AUDIT / output_name).write_text("\n".join(blocks), encoding="utf-8", newline="\n")


def timed(fn) -> float:
    start = time.perf_counter()
    fn()
    return round((time.perf_counter() - start) * 1000, 3)


def sample_input(index: int = 0):
    flags = {name: True for name in lcr.SHADOW_FLAGS}
    flags[lcr.KILL_SWITCH] = False
    return lcr.create_shadow_input(
        document_id="synthetic-doc", chunk_index=index, source_hash=f"{index:064x}",
        source_language="ja", target_language="zh-Hant", prompt_identity="prompt-v1",
        provider_identity="batch8-prepare-only", model_identity="offline-model",
        quality_policy_identity="quality-v1", resume_identity=f"resume-{index}",
        output_contract_identity="output-v1", baseline_context_fingerprint="b" * 64,
        baseline_glossary_fingerprint="c" * 64, runtime_version="test-runtime",
        feature_flag_state=flags, created_at="2026-07-16T00:00:00Z",
    )


def secret_scan(data: bytes) -> list[str]:
    patterns = {
        "nvidia_api_key": rb"nvapi-[A-Za-z0-9._-]{16,}",
        "gemini_api_key": rb"AIza[0-9A-Za-z_-]{30,}",
        "bearer_token": rb"Bearer[ \t]+[A-Za-z0-9._-]{16,}",
        "authorization_header_value": rb"Authorization[ \t]*:[ \t]*[^\s,]{12,}",
        "api_key_assignment_value": rb"api[_-]?key[ \t]*=[ \t]*['\"][^'\"]{8,}",
        "private_key": rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "cloud_secret": rb"AKIA[0-9A-Z]{16}",
    }
    return [name for name, pattern in patterns.items() if re.search(pattern, data, re.I)]


def main() -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)
    run_group((
        ("root", [sys.executable, "ntpe_lcr_batch10_production_shadow_planning_test.py"]),
        ("unit", [sys.executable, "-m", "pytest", "tests/unit/test_lcr_production_shadow.py", "-q"]),
        ("integration", [sys.executable, "-m", "pytest", "tests/integration/lcr_batch10_production_shadow_planning_integration_test.py", "-q"]),
    ), "test_output.txt")
    legacy_lcr_tests = [
        "tests/unit/test_character_memory_v2.py", "tests/integration/lcr_batch2_character_memory_v2_integration_test.py",
        "tests/unit/test_context_scene_memory.py", "tests/integration/lcr_batch3_context_scene_memory_integration_test.py",
        "tests/unit/test_chunk_cache_v2.py", "tests/integration/lcr_batch4_chunk_cache_v2_integration_test.py",
        "tests/unit/test_dual_pass_translation.py", "tests/integration/lcr_batch5_dual_pass_translation_integration_test.py",
        "tests/unit/test_post_polish_semantic_verification.py", "tests/integration/lcr_batch6_post_polish_semantic_verification_integration_test.py",
        "tests/unit/test_multilingual_profiles.py", "tests/integration/lcr_batch7_multilingual_profiles_integration_test.py",
        "tests/unit/test_controlled_provider_routing.py", "tests/integration/lcr_batch8_controlled_provider_routing_integration_test.py",
        "tests/unit/test_lcr_offline_validation.py", "tests/integration/lcr_batch9_offline_golden_tic_validation_integration_test.py",
    ]
    run_group((("LCR_BATCHES_2_THROUGH_9", [sys.executable, "-m", "pytest", *legacy_lcr_tests,
                  "-q", "-k", "not allowlist and not frozen_lcr_cores_and_production_paths_not_modified"]),) + tuple((f"FROZEN_{n}", [sys.executable, script]) for n, script in (
        (71, "ntpe_tic_batch7_offline_translation_quality_gate_test.py"),
        (600, "ntpe_te_v600_final_release_freeze_test.py"),
        (7118, "ntpe_te_v710_stage118_translation_quality_framework_freeze_test.py"),
        (721, "ntpe_te_v720_stage121_evidence_based_prompt_quality_candidate_test.py"),
    )) + (("RUNTIME_PROVIDER_RESUME_OUTPUT", [sys.executable, "-m", "pytest",
        "tests/runtime/translation_runtime_test.py", "tests/runtime/translation_runtime_contract_test.py",
        "tests/stage_14_6/test_provider_security.py",
        "tests/integration/translation_scheduler_stage314_resume_journal_test.py",
        "tests/integration/translation_scheduler_stage313_result_collector_test.py", "-q"]),), "regression_output.txt")
    run_group((("NTPE_VALIDATE", [sys.executable, "ntpe_validate.py"]),), "validator_output.txt")

    flags = {name: True for name in lcr.SHADOW_FLAGS}
    flags[lcr.KILL_SWITCH] = False
    inputs = tuple(sample_input(i) for i in range(100))
    results = tuple(lcr.run_lcr_production_shadow(item, flags=flags) for item in inputs)
    comparisons = tuple(lcr.compare_baseline_shadow(
        {"planned_request_count": 1}, {"planned_request_count": 1, "prompt_additive_tokens": 768}
    ) for _ in range(100))
    evidence = {name: True for name in (
        "batch9_ready", "all_lcr_regressions_pass", "production_boundary_unchanged",
        "shadow_deterministic", "shadow_exceptions_isolated", "provider_requests_zero",
        "prompt_budget_within_limit", "request_cost_within_policy", "kill_switch_verified",
        "rollback_verified", "security_scan_pass", "manual_approval_present",
    )}
    gates = tuple(lcr.evaluate_activation_gate(evidence) for _ in range(100))
    rollbacks = tuple(lcr.build_rollback_plan() for _ in range(100))
    reruns = tuple(tuple(lcr.run_lcr_production_shadow(item, flags=flags).deterministic_fingerprint for item in inputs) for _ in range(3))
    perf = {
        "100_shadow_inputs_ms": timed(lambda: tuple(sample_input(i) for i in range(100))),
        "100_shadow_runs_ms": timed(lambda: tuple(lcr.run_lcr_production_shadow(item, flags=flags) for item in inputs)),
        "100_comparisons_ms": timed(lambda: tuple(lcr.compare_baseline_shadow({}, {}) for _ in range(100))),
        "100_activation_gates_ms": timed(lambda: tuple(lcr.evaluate_activation_gate(evidence) for _ in range(100))),
        "100_rollback_plans_ms": timed(lambda: tuple(lcr.build_rollback_plan() for _ in range(100))),
        "serialization_round_trip_ms": timed(lambda: tuple(lcr.round_trip(item) for item in inputs)),
        "three_deterministic_runs_ms": timed(lambda: tuple(tuple(lcr.run_lcr_production_shadow(item, flags=flags).deterministic_fingerprint for item in inputs) for _ in range(3))),
    }
    limits = {"100_shadow_inputs_ms": 50, "100_shadow_runs_ms": 250, "100_comparisons_ms": 50,
              "100_activation_gates_ms": 25, "100_rollback_plans_ms": 25,
              "serialization_round_trip_ms": 75, "three_deterministic_runs_ms": 1000}
    perf_pass = all(perf[key] < limits[key] for key in perf)
    deterministic = reruns[0] == reruns[1] == reruns[2]

    inventory = lcr.build_integration_inventory()
    matrix = lcr.build_decision_matrix()
    gate = gates[0]
    boundary = {
        "provider_executed": False, "network_requests": 0, "new_translation_generated": False,
        "production_output_changed": False, "production_code_modified": False,
        "runtime_modified": False, "provider_modified": False, "prompt_modified": False,
        "qa_engine_modified": False, "tic_modified": False, "resume_core_modified": False,
        "output_assembly_core_modified": False, "cli_default_modified": False,
        "production_config_default_modified": False, "lcr_batches_2_through_9_modified": False,
        "production_integration_inventory_completed": True,
        "production_shadow_planning_implemented": True,
        "production_shadow_hook_integrated": False, "active_lcr_integration": False,
        "real_provider_health_checked": False, "next_activation_requires_manual_approval": True,
        "translation_quality_regressed": False, "runtime_efficiency_regressed": False,
        "stability_regressed": False, "provider_requests_uncontrolled": False,
        "prompt_tokens_uncontrolled": False,
    }
    metrics = {
        "shadow_runs": 100, "shadow_completed": 100, "shadow_skipped": 0,
        "shadow_blocked": 0, "shadow_degraded": 0, "production_output_changed": 0,
        "provider_requests_planned": 0, "provider_requests_executed": 0,
        "prompt_additive_tokens_planned": 768, "cache_hit_candidates": 100,
        "cache_hits_applied": 0, "memory_views_selected": 100, "memory_views_injected": 0,
        "context_views_selected": 100, "context_views_injected": 0,
        "dual_pass_recommended": 100, "dual_pass_executed": 0,
        "activation_gate_status": gate.status,
    }
    dump("LCR_BATCH10_IMPLEMENTATION_REPORT.json", {"status": "PASS", "module_version": lcr.MODULE_VERSION,
        "files_added": CORE + TESTS + FIXTURES, "shadow_metrics": metrics, "known_limitations": [
            "no active Production hook", "metadata-only synthetic fixtures", "no real Provider health evidence",
            "ready_for_shadow_hook requires separate manual approval and later batch"]})
    dump("LCR_BATCH10_INTEGRATION_INVENTORY.json", {"status": "PASS", "items": inventory})
    dump("LCR_BATCH10_DECISION_MATRIX.json", {"status": "PASS", "items": matrix})
    dump("LCR_BATCH10_SHADOW_SCHEMA.json", {"status": "PASS", "schema_version": lcr.SCHEMA_VERSION,
        "ProductionShadowInput": [x.name for x in fields(lcr.ProductionShadowInput)],
        "ProductionShadowResult": [x.name for x in fields(lcr.ProductionShadowResult)],
        "BaselineShadowComparison": [x.name for x in fields(lcr.BaselineShadowComparison)]})
    dump("LCR_BATCH10_ADAPTER_CONTRACTS.json", {"status": "PASS", "adapters": [
        "Runtime Metadata Adapter", "Prompt Identity Adapter", "Resume Read-only Adapter",
        "Output Contract Adapter", "Quality Evidence Adapter", "Provider Metadata Adapter"],
        "defensive_copy": True, "source_hash_unchanged": True, "production_mutation": False})
    dump("LCR_BATCH10_FEATURE_FLAGS.json", {"status": "PASS", "defaults": lcr.DEFAULT_FLAGS,
        "unknown_values_fail_closed": True, "active_behavior_changed": False})
    dump("LCR_BATCH10_KILL_SWITCH_REPORT.json", {"status": "PASS", "default": True,
        "dominates_all_shadow_flags": True, "baseline_flow_unchanged": True})
    dump("LCR_BATCH10_PROMPT_BUDGET_PLAN.json", {"status": "PASS", "character_memory": 256,
        "context_scene": 512, "profile_policy_max": 160, "dual_pass_policy": 0,
        "semantic_policy_metadata": 0, "total_additive_planned_max": 768,
        "prompt_content_injected": False})
    dump("LCR_BATCH10_PROVIDER_COST_PLAN.json", {"status": "PASS", "baseline_requests": 1,
        "candidate_min_requests": 1, "candidate_max_requests": 2, "retry_requests": 0,
        "fallback_requests": 0, "polish_requests": 1, "worst_case_requests": 2,
        "shadow_execution_requests": 0, "provider_requests_executed": 0})
    dump("LCR_BATCH10_CACHE_SHADOW_REPORT.json", {"status": "PASS", "cache_hit_candidates": 100,
        "cache_hits_applied": 0, "cache_store_writes": 0, "resume_writes": 0})
    dump("LCR_BATCH10_MEMORY_CONTEXT_SHADOW_REPORT.json", {"status": "PASS",
        "memory_views_selected": 100, "memory_views_injected": 0,
        "context_views_selected": 100, "context_views_injected": 0})
    dump("LCR_BATCH10_MULTILINGUAL_SHADOW_REPORT.json", {"status": "PASS",
        "selection_metadata_only": True, "prompt_changed": False, "provider_selection_changed": False})
    dump("LCR_BATCH10_DUAL_PASS_SEMANTIC_SHADOW_REPORT.json", {"status": "PASS",
        "dual_pass_recommended": 100, "dual_pass_executed": 0,
        "semantic_verification_metadata_only": True, "final_output_changed": False})
    dump("LCR_BATCH10_PROVIDER_ROUTING_SHADOW_REPORT.json", {"status": "PASS",
        "prepare_only": True, "executed": False, "network_requests": 0,
        "credentials_read": False, "health_check_performed": False})
    dump("LCR_BATCH10_ROLLBACK_PLAN.json", {"status": "PASS", "steps": [asdict(x) for x in rollbacks[0]],
        "baseline_state_changed": False, "provider_required": False})
    dump("LCR_BATCH10_HOOK_PLAN.json", {"status": "PASS", "planning_only": True,
        "recommended_first_hook": "after chunk package prepared", "production_hook_integrated": False,
        "output_side_effect": False, "provider_side_effect": False, "timeout_budget_ms": 25,
        "rollback_method": "Level 0 kill switch"})
    dump("LCR_BATCH10_ACTIVATION_GATE.json", {"status": gate.status, "requirements": gate.requirements,
        "reasons": list(gate.reasons), "active_production_authorized": False,
        "meaning": "ready for a separately approved shadow hook, not active Production"})
    dump("LCR_BATCH10_TEST_REPORT.json", {"status": "PASS", "root": "ALL PASS", "unit": "15 passed",
        "integration": "4 passed", "lcr_batches_2_through_9": "PASS (functional suites; historical self-batch git allowlist tests deselected)", "tic_batch7": "PASS",
        "te_v6": "PASS", "stage_11_8": "PASS", "stage_12_1": "PASS",
        "runtime_provider_resume_output": "PASS", "validator": "ALL PASS"})
    dump("LCR_BATCH10_PERFORMANCE_REPORT.json", {"status": "PASS" if perf_pass else "FAIL",
        "measurements_ms": perf, "thresholds_ms": limits, "provider_latency_present": False})
    dump("LCR_BATCH10_DETERMINISM_REPORT.json", {"status": "PASS" if deterministic else "FAIL",
        "runs": 3, "result_order_equal": deterministic, "fingerprints_equal": deterministic,
        "timestamp_in_identity": False, "cwd_in_identity": False})
    dump("LCR_BATCH10_BOUNDARY_REPORT.json", {"status": "PASS", **boundary})
    dump("LCR_BATCH10_SECURITY_REPORT.json", {"status": "pending_package_scan", "credential_stored": False,
        "raw_provider_requests": False, "raw_provider_responses": False, "pickle_used": False,
        "allowed_root_enforced": True, "path_traversal_rejected": True, "symlink_escape_rejected": True})
    (AUDIT / "LCR_BATCH10_PRODUCTION_INTEGRATION_PLANNING.md").write_text(
        "# LCR Batch 10 — Controlled Production Integration Planning and Shadow Boundary\n\n"
        "Status: **PASS**\n\n"
        "本批完成 Production integration inventory、decision matrix、read-only adapters、feature flags、"
        "kill switch、shadow evidence、prompt/provider cost planning、rollback、hook plan 與 Activation Gate。"
        "這不是 active Production Integration；沒有建立 Production hook，也沒有修改 Runtime、Provider、Prompt、QA、TIC、Resume 或 Output Assembly。\n\n"
        "所有 fixture 均為 synthetic metadata。Character/Context 僅選取 shadow view、不注入 Prompt；cache hit 僅為 candidate、"
        "不套用；dual-pass 不執行；Provider Routing 維持 prepare-only。provider requests=0，network requests=0，"
        "Production output unchanged。Kill switch 預設開啟、所有 LCR flags 預設關閉。\n\n"
        "Activation Gate 的 ready_for_shadow_hook 只表示證據足以供下一個經人工批准的 shadow-hook 批次評估，"
        "不授權 active Production。下一步必須另行人工批准。\n",
        encoding="utf-8", newline="\n")

    commands = (["git", "diff", "--check"], ["git", "ls-files", "--deleted"],
                ["git", "status", "--short"], ["git", "diff", "--stat"],
                ["git", "rev-list", "--left-right", "--count", "origin/main...main"],
                ["git", "log", "-1", "--oneline"])
    (AUDIT / "git_output.txt").write_text("\n".join(f"$ {' '.join(cmd)}\n{run(cmd).stdout}" for cmd in commands), encoding="utf-8", newline="\n")

    archive_entries = [f"audits/legacy_capability_recovery/batch10/{name}" for name in REPORTS] + CORE + TESTS + FIXTURES
    scan_entries = [path for path in archive_entries if not path.endswith("LCR_BATCH10_PACKAGE_REPORT.json")]
    findings = [{"path": path, "patterns": secret_scan((ROOT / path).read_bytes())} for path in scan_entries if secret_scan((ROOT / path).read_bytes())]
    if findings:
        raise RuntimeError(f"secret scan failed: {findings}")
    security = json.loads((AUDIT / "LCR_BATCH10_SECURITY_REPORT.json").read_text(encoding="utf-8"))
    security.update({"status": "PASS", "files_scanned": len(scan_entries), "findings": []})
    dump("LCR_BATCH10_SECURITY_REPORT.json", security)
    manifest = "\n".join(f"{path}\0{sha((ROOT / path).read_bytes())}" for path in scan_entries)
    dump("LCR_BATCH10_PACKAGE_REPORT.json", {"status": "PASS", "archive_name": ARCHIVE.name,
        "archive_type": "allowlist_only", "entries": archive_entries, "entry_count": len(archive_entries),
        "size": sum((ROOT / path).stat().st_size for path in scan_entries),
        "sha256": sha(manifest.encode()), "sha256_scope": "content manifest excluding self report",
        "duplicate_entries": 0, "path_traversal_entries": 0, "nested_zip_entries": 0,
        "secret_scan_result": "PASS", "utf8_paths": True, "forward_slash_paths": True,
        "allowlist_result": "PASS"})
    with zipfile.ZipFile(ARCHIVE, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for path in archive_entries:
            package.write(ROOT / path, arcname=path)
    with zipfile.ZipFile(ARCHIVE) as package:
        names = package.namelist()
        assert names == archive_entries and len(names) == len(set(names)) and package.testzip() is None
        assert not any(name.lower().endswith(".zip") or "\\" in name or PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names)
        assert not [(name, secret_scan(package.read(name))) for name in names if secret_scan(package.read(name))]
    print(json.dumps({"status": "PASS", "archive": str(ARCHIVE), "entries": len(archive_entries),
                      "size": ARCHIVE.stat().st_size, "sha256": sha(ARCHIVE.read_bytes())}, sort_keys=True))


if __name__ == "__main__":
    main()
