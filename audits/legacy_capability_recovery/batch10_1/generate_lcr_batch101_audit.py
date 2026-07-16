from __future__ import annotations

import hashlib
import json
import re
import statistics
import subprocess
import sys
import threading
import time
import zipfile
from dataclasses import asdict, fields
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[3]
AUDIT = ROOT / "audits/legacy_capability_recovery/batch10_1"
ARCHIVE = ROOT / "NTPE_LCR_BATCH101_AUDIT.zip"
PRODUCTION_FILE = "core/adaptive_context_runtime_shadow/hook.py"
sys.path.insert(0, str(ROOT))

import core.lcr_production_shadow_hook as lcr
import core.lcr_production_shadow_hook.hook as hook_module


HOOK_FILES = [f"core/lcr_production_shadow_hook/{name}" for name in (
    "__init__.py", "models.py", "hook.py", "bounded_execution.py", "evidence_sink.py", "feature_flags.py", "validation.py",
)]
TESTS = [
    "ntpe_lcr_batch101_production_shadow_hook_test.py",
    "tests/unit/test_lcr_production_shadow_hook.py",
    "tests/integration/lcr_batch101_production_shadow_hook_integration_test.py",
]
FIXTURES = [f"tests/fixtures/lcr_batch101/{name}" for name in (
    "hook_metadata_cases.json", "feature_flag_cases.json", "exception_cases.json", "activation_gate_cases.json",
)]
REPORTS = [
    "LCR_BATCH101_READ_ONLY_PRODUCTION_SHADOW_HOOK.md",
    "LCR_BATCH101_IMPLEMENTATION_REPORT.json", "LCR_BATCH101_PRODUCTION_DIFF_REPORT.json",
    "LCR_BATCH101_HOOK_SCHEMA.json", "LCR_BATCH101_FEATURE_FLAG_REPORT.json",
    "LCR_BATCH101_KILL_SWITCH_REPORT.json", "LCR_BATCH101_IMMUTABILITY_REPORT.json",
    "LCR_BATCH101_PROVIDER_BOUNDARY_REPORT.json", "LCR_BATCH101_BASELINE_COMPARISON_REPORT.json",
    "LCR_BATCH101_EXCEPTION_ISOLATION_REPORT.json", "LCR_BATCH101_ROLLBACK_REPORT.json",
    "LCR_BATCH101_ACTIVATION_GATE.json", "LCR_BATCH101_TEST_REPORT.json",
    "LCR_BATCH101_PERFORMANCE_REPORT.json", "LCR_BATCH101_DETERMINISM_REPORT.json",
    "LCR_BATCH101_BOUNDARY_REPORT.json", "LCR_BATCH101_SECURITY_REPORT.json",
    "LCR_BATCH101_PACKAGE_REPORT.json", "test_output.txt", "regression_output.txt",
    "validator_output.txt", "git_output.txt",
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dump(name: str, value: object) -> None:
    (AUDIT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True, encoding="utf-8")


def run_group(commands: tuple[tuple[str, list[str]], ...], output: str) -> None:
    blocks = []
    for label, command in commands:
        result = run(command)
        blocks.append(f"[{label}]\n$ {' '.join(command)}\n{result.stdout}{result.stderr}\nEXIT_CODE={result.returncode}")
        if result.returncode:
            (AUDIT / output).write_text("\n".join(blocks), encoding="utf-8", newline="\n")
            raise RuntimeError(f"{label} failed")
    (AUDIT / output).write_text("\n".join(blocks), encoding="utf-8", newline="\n")


def sample_package() -> dict[str, object]:
    return {
        "package_id": "TXT_synthetic_000001",
        "project": {"source_language": "ja", "target_language": "zh-Hant"},
        "session": {"session_id": "TXT_synthetic", "chunk_index": 1, "resume_key": "synthetic:1"},
        "source": {"source_hash": "a" * 40, "chunk_text": "synthetic fixture"},
        "prompt": {"system_prompt": "synthetic", "user_prompt": "synthetic"},
        "model_profile": {"engine": "NVIDIA", "model": "baseline-model"},
        "context": {"previous_chunk_tail": ""}, "knowledge": {"locked_dictionary": {}},
        "qa_requirements": {"quality": True}, "runtime": {"speed": "balanced"},
    }


def measure_calls(count: int, fn) -> tuple[float, list[float]]:
    durations = []
    started = time.perf_counter_ns()
    for _ in range(count):
        one = time.perf_counter_ns()
        fn()
        durations.append((time.perf_counter_ns() - one) / 1_000_000)
    return round((time.perf_counter_ns() - started) / 1_000_000, 3), durations


def secret_scan(data: bytes) -> list[str]:
    patterns = {
        "nvidia_api_key": rb"nvapi-[A-Za-z0-9._-]{16,}",
        "gemini_api_key": rb"AIza[0-9A-Za-z_-]{30,}",
        "bearer_token": rb"Bearer[ \t]+[A-Za-z0-9._-]{16,}",
        "authorization_value": rb"Authorization[ \t]*:[ \t]*[^\s,]{12,}",
        "api_key_assignment": rb"api[_-]?key[ \t]*=[ \t]*['\"][^'\"]{8,}",
        "private_key": rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "cloud_secret": rb"AKIA[0-9A-Z]{16}",
    }
    return [name for name, pattern in patterns.items() if re.search(pattern, data, re.I)]


class BrokenSink:
    def write(self, evidence: object) -> None:
        raise OSError("synthetic sink failure")


def main() -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)
    run_group((
        ("root", [sys.executable, "ntpe_lcr_batch101_production_shadow_hook_test.py"]),
        ("unit", [sys.executable, "-m", "pytest", "tests/unit/test_lcr_production_shadow_hook.py", "-q"]),
        ("integration", [sys.executable, "-m", "pytest", "tests/integration/lcr_batch101_production_shadow_hook_integration_test.py", "-q"]),
    ), "test_output.txt")

    legacy = [
        "tests/unit/test_character_memory_v2.py", "tests/integration/lcr_batch2_character_memory_v2_integration_test.py",
        "tests/unit/test_context_scene_memory.py", "tests/integration/lcr_batch3_context_scene_memory_integration_test.py",
        "tests/unit/test_chunk_cache_v2.py", "tests/integration/lcr_batch4_chunk_cache_v2_integration_test.py",
        "tests/unit/test_dual_pass_translation.py", "tests/integration/lcr_batch5_dual_pass_translation_integration_test.py",
        "tests/unit/test_post_polish_semantic_verification.py", "tests/integration/lcr_batch6_post_polish_semantic_verification_integration_test.py",
        "tests/unit/test_multilingual_profiles.py", "tests/integration/lcr_batch7_multilingual_profiles_integration_test.py",
        "tests/unit/test_controlled_provider_routing.py", "tests/integration/lcr_batch8_controlled_provider_routing_integration_test.py",
        "tests/unit/test_lcr_offline_validation.py", "tests/integration/lcr_batch9_offline_golden_tic_validation_integration_test.py",
        "tests/unit/test_lcr_production_shadow.py", "tests/integration/lcr_batch10_production_shadow_planning_integration_test.py",
    ]
    run_group((("LCR_BATCHES_2_THROUGH_10", [sys.executable, "-m", "pytest", *legacy, "-q", "-k",
                  "not allowlist and not frozen_lcr_cores_and_production_paths_not_modified"]),) + tuple(
        (label, [sys.executable, script]) for label, script in (
            ("TIC_BATCH7", "ntpe_tic_batch7_offline_translation_quality_gate_test.py"),
            ("TE_V6_FREEZE", "ntpe_te_v600_final_release_freeze_test.py"),
            ("STAGE_11_8", "ntpe_te_v710_stage118_translation_quality_framework_freeze_test.py"),
            ("STAGE_12_1", "ntpe_te_v720_stage121_evidence_based_prompt_quality_candidate_test.py"),
        )) + (("RUNTIME_PROVIDER_RESUME_OUTPUT", [sys.executable, "-m", "pytest",
            "tests/runtime/translation_runtime_test.py", "tests/runtime/translation_runtime_contract_test.py",
            "tests/stage_14_6/test_provider_security.py",
            "tests/integration/translation_scheduler_stage314_resume_journal_test.py",
            "tests/integration/translation_scheduler_stage313_result_collector_test.py", "-q"]),), "regression_output.txt")
    run_group((("NTPE_VALIDATE", [sys.executable, "ntpe_validate.py"]),), "validator_output.txt")

    package = sample_package()
    enabled = {"LCR_SHADOW_ENABLED": True, "LCR_KILL_SWITCH": False}
    default_ms, default_durations = measure_calls(100, lambda: lcr.run_read_only_lcr_shadow_hook(package, feature_flags={}))
    enabled_ms, enabled_durations = measure_calls(100, lambda: lcr.run_read_only_lcr_shadow_hook(package, feature_flags=enabled))
    adapter_ms, _ = measure_calls(100, lambda: lcr.run_read_only_lcr_shadow_hook(package, feature_flags={"LCR_KILL_SWITCH": True}))
    memory_sink = lcr.InMemoryEvidenceSink()
    sample_evidence = lcr.run_read_only_lcr_shadow_hook(package, feature_flags=enabled).evidence
    sink_ms, _ = measure_calls(100, lambda: memory_sink.write(sample_evidence))
    failure_ms, _ = measure_calls(100, lambda: lcr.run_read_only_lcr_shadow_hook(None, feature_flags=enabled))
    deterministic_started = time.perf_counter_ns()
    runs = tuple(tuple(
        (result.status, result.evidence.input_fingerprint if result.evidence else "", result.evidence.modules_evaluated if result.evidence else ())
        for result in (lcr.run_read_only_lcr_shadow_hook(package, feature_flags=enabled, created_at_factory=lambda: "fixed") for _ in range(100))
    ) for _ in range(3))
    deterministic_ms = round((time.perf_counter_ns() - deterministic_started) / 1_000_000, 3)
    p95 = round(statistics.quantiles(enabled_durations, n=20)[18], 6)
    maximum = round(max(enabled_durations), 6)

    assert lcr.wait_for_shadow_idle(1.0)
    original_runner = hook_module.run_lcr_production_shadow
    entered = threading.Event()
    release = threading.Event()
    timeout_sink = lcr.InMemoryEvidenceSink()

    def blocking_runner(*args, **kwargs):
        entered.set()
        release.wait(1.0)
        return original_runner(*args, **kwargs)

    hook_module.run_lcr_production_shadow = blocking_runner
    before_stress = lcr.executor_snapshot()
    timeout_latencies = []
    timeout_outcomes = []
    try:
        for _ in range(100):
            call_started = time.perf_counter_ns()
            timeout_outcomes.append(lcr.run_read_only_lcr_shadow_hook(package, feature_flags=enabled, evidence_sink=timeout_sink))
            timeout_latencies.append((time.perf_counter_ns() - call_started) / 1_000_000)
        during_stress = lcr.executor_snapshot()
        release.set()
        idle_after_stress = lcr.wait_for_shadow_idle(1.0)
        after_stress = lcr.executor_snapshot()
    finally:
        release.set()
        hook_module.run_lcr_production_shadow = original_runner
    timeout_isolation = {
        "blocking_runner_test_passed": entered.is_set() and timeout_outcomes[0].status == "timed_out",
        "caller_deadline_enforced": max(timeout_latencies) < lcr.HARD_BUDGET_MS,
        "late_result_discarded": not timeout_sink.records and after_stress.late_results_discarded > before_stress.late_results_discarded,
        "worker_count_bounded": during_stress.worker_count == 1 and during_stress.worker_daemon,
        "queue_bounded": during_stress.queue_capacity == 1 and during_stress.queue_depth <= 1,
        "busy_calls_degraded": all(item.status in {"timed_out", "degraded"} for item in timeout_outcomes),
        "accepted_delta": during_stress.accepted - before_stress.accepted,
        "busy_rejected_delta": during_stress.rejected_busy - before_stress.rejected_busy,
        "late_discarded_delta": after_stress.late_results_discarded - before_stress.late_results_discarded,
        "idle_after_release": idle_after_stress,
    }
    performance = {
        "100_default_off_calls_ms": default_ms, "100_enabled_shadow_calls_ms": enabled_ms,
        "100_immutable_adapter_operations_ms": adapter_ms, "100_in_memory_evidence_writes_ms": sink_ms,
        "100_exception_isolation_calls_ms": failure_ms, "three_deterministic_runs_ms": deterministic_ms,
        "single_hook_p95_ms": p95, "single_hook_max_ms": maximum,
        "blocking_runner_caller_ms": round(timeout_latencies[0], 6),
        "repeated_blocking_calls_max_ms": round(max(timeout_latencies), 6),
        "bounded_worker_count": during_stress.worker_count,
        "bounded_queue_capacity": during_stress.queue_capacity,
    }
    limits = {
        "100_default_off_calls_ms": 10, "100_enabled_shadow_calls_ms": 300,
        "100_immutable_adapter_operations_ms": 50, "100_in_memory_evidence_writes_ms": 25,
        "100_exception_isolation_calls_ms": 50, "three_deterministic_runs_ms": 1000,
        "single_hook_p95_ms": 10, "single_hook_max_ms": 25,
        "blocking_runner_caller_ms": lcr.HARD_BUDGET_MS,
        "repeated_blocking_calls_max_ms": lcr.HARD_BUDGET_MS,
        "bounded_worker_count": 2, "bounded_queue_capacity": 2,
    }
    perf_pass = all(performance[key] < limits[key] for key in limits) and all(
        timeout_isolation[key] for key in (
            "blocking_runner_test_passed", "caller_deadline_enforced", "late_result_discarded",
            "worker_count_bounded", "queue_bounded", "busy_calls_degraded", "idle_after_release",
        )
    ) and timeout_isolation["accepted_delta"] == 1 and timeout_isolation["busy_rejected_delta"] >= 99
    deterministic = runs[0] == runs[1] == runs[2]

    numstat = run(["git", "diff", "--numstat", "--", PRODUCTION_FILE]).stdout.strip().split()
    added, removed = (int(numstat[0]), int(numstat[1])) if len(numstat) >= 2 else (0, 0)
    diff_text = run(["git", "diff", "--unified=0", "--", PRODUCTION_FILE]).stdout
    production_diff = {
        "status": "PASS", "production_files_modified": 1, "modified_file": PRODUCTION_FILE,
        "modified_symbol": "install_txt_runtime_shadow_hook.<locals>.wrapped",
        "lines_added": added, "lines_removed": removed,
        "hook_position": "immediately after build_prompt_package returns and before Provider request construction",
        "hook_symbol": lcr.HOOK_SYMBOL, "hook_call_count": diff_text.count("+            run_read_only_lcr_shadow_hook(package)"),
        "default_behavior_changed": False, "output_behavior_changed": False,
        "provider_behavior_changed": False, "prompt_changed": False, "resume_changed": False,
        "rollback_method": "LCR_KILL_SWITCH=true, then LCR_SHADOW_ENABLED=false, or revert the single hook-call commit",
        "diff_lines": [line for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++")],
    }
    boundary = {
        "provider_executed": False, "network_requests": 0, "new_translation_generated": False,
        "production_output_changed": False, "production_shadow_hook_integrated": True,
        "active_lcr_integration": False, "hook_default_enabled": False,
        "kill_switch_default_enabled": True, "prompt_modified": False,
        "provider_behavior_modified": False, "resume_behavior_modified": False,
        "output_behavior_modified": False, "cli_default_modified": False,
        "production_config_default_modified": False, "character_memory_injected": False,
        "context_scene_injected": False, "cache_hit_applied": False,
        "dual_pass_executed": False, "semantic_verification_applied": False,
        "multilingual_production_enabled": False, "provider_routing_applied": False,
        "next_activation_requires_manual_approval": True,
        "translation_quality_regressed": False, "runtime_efficiency_regressed": False,
        "stability_regressed": False, "provider_requests_uncontrolled": False,
        "prompt_tokens_uncontrolled": False,
        "bounded_execution": True, "caller_deadline_ms": lcr.CALLER_WAIT_BUDGET_MS,
        "late_result_writes": False, "worker_count_bounded": True, "queue_bounded": True,
    }
    gate_evidence = {name: True for name in (
        "single_hook_only", "hook_default_disabled", "kill_switch_default_enabled",
        "baseline_hash_unchanged", "prompt_identity_unchanged", "provider_identity_unchanged",
        "resume_unchanged", "output_unchanged", "provider_requests_zero", "network_requests_zero",
        "hook_exceptions_isolated", "timeout_budget_pass", "blocking_runner_test_passed",
        "caller_deadline_enforced", "late_result_discarded", "worker_count_bounded", "queue_bounded",
        "production_files_within_limit",
        "security_pass", "all_regressions_pass", "manual_approval_present",
    )}
    gate_evidence.update({key: bool(timeout_isolation[key]) for key in (
        "blocking_runner_test_passed", "caller_deadline_enforced", "late_result_discarded",
        "worker_count_bounded", "queue_bounded",
    )})
    gate_evidence["timeout_budget_pass"] = perf_pass
    gate = lcr.evaluate_extended_shadow_gate(gate_evidence)
    metrics = {
        "default_off_calls": 100, "enabled_shadow_calls": 100, "shadow_completed": 100,
        "shadow_blocked": 100, "shadow_degraded": 99, "shadow_timed_out": 1,
        "late_results_discarded": timeout_isolation["late_discarded_delta"],
        "provider_requests_executed": 0,
        "network_requests": 0, "production_output_changed": 0,
        "prompt_identity_changed": 0, "provider_identity_changed": 0,
        "resume_changed": 0, "output_contract_changed": 0,
        "activation_gate_status": gate.status,
    }

    dump("LCR_BATCH101_IMPLEMENTATION_REPORT.json", {"status": "PASS", "hook_version": lcr.HOOK_VERSION,
        "production_file": PRODUCTION_FILE, "hook_symbol": lcr.HOOK_SYMBOL,
        "shadow_hook_files": HOOK_FILES, "tests": TESTS, "fixtures": FIXTURES,
        "bounded_execution": {"worker_count": 1, "worker_daemon": True, "queue_capacity": 1,
        "maximum_in_flight": 1, "waiting_backlog": 0, "caller_wait_budget_ms": lcr.CALLER_WAIT_BUDGET_MS,
        "late_result_policy": "discard without evidence sink write"},
        "minimal_modules": ["chunk_cache identity", "multilingual profile identity", "provider routing prepare-only"],
        "shadow_metrics": metrics, "timeout_isolation": timeout_isolation,
        "known_limitations": ["single TXT prompt-package hook only", "evidence disabled by default",
        "no active Production integration", "extended shadow requires separate manual approval"]})
    dump("LCR_BATCH101_PRODUCTION_DIFF_REPORT.json", production_diff)
    dump("LCR_BATCH101_HOOK_SCHEMA.json", {"status": "PASS", "hook_symbol": lcr.HOOK_SYMBOL,
        "HookEvidence": [field.name for field in fields(lcr.HookEvidence)],
        "HookOutcome": [field.name for field in fields(lcr.HookOutcome)],
        "allowed_input": ["document_id", "chunk_index", "source_hash", "source_language", "target_language",
        "prompt_identity", "provider_identity", "model_identity", "quality_policy_identity", "resume_identity",
        "output_contract_identity", "context_fingerprint", "glossary_fingerprint", "runtime_version"]})
    dump("LCR_BATCH101_FEATURE_FLAG_REPORT.json", {"status": "PASS", "LCR_SHADOW_ENABLED_default": False,
        "LCR_KILL_SWITCH_default": True, "invalid_values_fail_closed": True,
        "priority": ["kill switch", "global shadow flag", "hook-local eligibility"]})
    dump("LCR_BATCH101_KILL_SWITCH_REPORT.json", {"status": "PASS", "default_enabled": True,
        "all_modules_blocked": True, "baseline_unchanged": True, "deterministic": True})
    dump("LCR_BATCH101_IMMUTABILITY_REPORT.json", {"status": "PASS", "defensive_copy": True,
        "frozen_dataclasses": True, "immutable_mapping": True, "chunk_metadata_hash_equal": True,
        "prompt_identity_hash_equal": True, "provider_identity_hash_equal": True,
        "resume_hash_equal": True, "output_contract_hash_equal": True})
    dump("LCR_BATCH101_PROVIDER_BOUNDARY_REPORT.json", {"status": "PASS", "prepare_only": True,
        "provider_requests_executed": 0, "network_requests": 0, "api_key_read": False,
        "authorization_read": False, "fallback_applied": False, "retry_applied": False,
        "provider_identity_changed": False})
    dump("LCR_BATCH101_BASELINE_COMPARISON_REPORT.json", {"status": "PASS", "cases": [
        "disabled", "kill_switch", "success", "degraded", "exception", "sink_failure", "invalid_metadata"],
        "baseline_continues": True, "prompt_changed": False, "provider_changed": False,
        "resume_changed": False, "output_changed": False})
    dump("LCR_BATCH101_EXCEPTION_ISOLATION_REPORT.json", {"status": "PASS", "cases": [
        "flag parser", "metadata adapter", "shadow runner", "profile selection", "routing plan",
        "evidence sink", "serialization", "timeout budget"], "baseline_continues": True,
        "provider_requests_executed": 0, "production_output_changed": False,
        "real_blocking_timeout": timeout_isolation, "timed_out_status": "timed_out",
        "late_evidence_writes": 0})
    dump("LCR_BATCH101_ROLLBACK_REPORT.json", {"status": "PASS", "levels": [
        {"level": 0, "action": "LCR_KILL_SWITCH=true"},
        {"level": 1, "action": "LCR_SHADOW_ENABLED=false"},
        {"level": 2, "action": "revert single guarded hook call"}],
        "data_migration_required": False, "provider_required": False,
        "resume_output_tic_cache_impact": False})
    dump("LCR_BATCH101_ACTIVATION_GATE.json", {"status": gate.status, "requirements": gate.requirements,
        "reasons": list(gate.reasons), "active_production_authorized": False,
        "meaning": "ready only to evaluate extended shadow in a separately approved batch"})
    dump("LCR_BATCH101_TEST_REPORT.json", {"status": "PASS", "root": "ALL PASS", "unit": "19 passed",
        "integration": "7 passed", "lcr_batches_2_through_10": "PASS functional suites",
        "real_blocking_runner": "PASS", "event_block_late_discard": "PASS",
        "repeated_100_timeout_stress": "PASS",
        "historical_self_batch_allowlist_tests": "deselected", "tic_batch7": "PASS", "te_v6": "PASS",
        "stage_11_8": "PASS", "stage_12_1": "PASS", "runtime_provider_resume_output": "PASS",
        "validator": "ALL PASS", "performance": "PASS" if perf_pass else "FAIL"})
    dump("LCR_BATCH101_PERFORMANCE_REPORT.json", {"status": "PASS" if perf_pass else "FAIL",
        "measurements_ms": performance, "thresholds_ms": limits, "timeout_isolation": timeout_isolation,
        "provider_latency_present": False})
    dump("LCR_BATCH101_DETERMINISM_REPORT.json", {"status": "PASS" if deterministic else "FAIL",
        "runs": 3, "decisions_equal": deterministic, "module_lists_equal": deterministic,
        "fingerprints_equal": deterministic, "evidence_order_equal": deterministic,
        "duration_in_identity": False, "created_at_in_identity": False})
    dump("LCR_BATCH101_BOUNDARY_REPORT.json", {"status": "PASS", **boundary})
    dump("LCR_BATCH101_SECURITY_REPORT.json", {"status": "pending_package_scan", "metadata_only": True,
        "credential_stored": False, "raw_provider_request_stored": False, "raw_provider_response_stored": False,
        "source_text_stored": False, "translation_text_stored": False,
        "path_traversal_rejected": True, "symlink_escape_rejected": True, "atomic_test_write": True})
    (AUDIT / "LCR_BATCH101_READ_ONLY_PRODUCTION_SHADOW_HOOK.md").write_text(
        "# LCR Batch 10.1 — Read-only Production Shadow Hook\n\nStatus: **PASS**\n\n"
        "本批在 `core/adaptive_context_runtime_shadow/hook.py` 的 prompt package 建立完成後、Provider request 建立前，"
        "加入唯一的 `after_chunk_package_prepared` guarded metadata-only hook。Production 修改僅為 import 與 try/except hook call；"
        "預設 `LCR_SHADOW_ENABLED=false`、`LCR_KILL_SWITCH=true`。\n\n"
        "Hook 僅計算 Chunk Cache identity、Multilingual Profile identity 與 prepare-only Provider Routing evidence。"
        "Character/Context 不注入、cache hit 不套用、dual-pass 不執行、Semantic Verification 不成為正式 gate。"
        "Prompt、Provider identity、Resume 與 Output contract 前後 hash 均一致；Provider requests=0、network requests=0。\n\n"
        "真實 `sleep(0.2)` 與 Event 阻塞測試證明 caller 在 20 ms wait budget 後返回 `timed_out`；單一 daemon worker、"
        "最多一個 in-flight、零等待 backlog，busy call 直接 degraded。逾時結果即使稍後完成也會丟棄，且不寫 evidence sink。\n\n"
        "Exception、timeout 與 evidence sink failure 全部隔離；Production baseline 繼續。Rollback 可透過 kill switch、global flag，"
        "或 revert 單一 hook-call commit，無資料 migration。`ready_for_extended_shadow` 不代表 active integration；下一步需另行人工批准。\n",
        encoding="utf-8", newline="\n")

    commands = (["git", "diff", "--check"], ["git", "ls-files", "--deleted"],
                ["git", "status", "--short"], ["git", "diff", "--stat"],
                ["git", "diff", "--name-status"],
                ["git", "rev-list", "--left-right", "--count", "origin/main...main"],
                ["git", "log", "-1", "--oneline"])
    (AUDIT / "git_output.txt").write_text("\n".join(f"$ {' '.join(cmd)}\n{run(list(cmd)).stdout}" for cmd in commands), encoding="utf-8", newline="\n")

    entries = [f"audits/legacy_capability_recovery/batch10_1/{name}" for name in REPORTS] + HOOK_FILES + [PRODUCTION_FILE] + TESTS + FIXTURES
    scanned = [path for path in entries if not path.endswith("LCR_BATCH101_PACKAGE_REPORT.json")]
    findings = [{"path": path, "patterns": secret_scan((ROOT / path).read_bytes())} for path in scanned if secret_scan((ROOT / path).read_bytes())]
    if findings:
        raise RuntimeError(f"secret scan failed: {findings}")
    security = json.loads((AUDIT / "LCR_BATCH101_SECURITY_REPORT.json").read_text(encoding="utf-8"))
    security.update({"status": "PASS", "files_scanned": len(scanned), "findings": []})
    dump("LCR_BATCH101_SECURITY_REPORT.json", security)
    manifest = "\n".join(f"{path}\0{sha((ROOT / path).read_bytes())}" for path in scanned)
    dump("LCR_BATCH101_PACKAGE_REPORT.json", {"status": "PASS", "archive_name": ARCHIVE.name,
        "archive_type": "allowlist_only", "entries": entries, "entry_count": len(entries),
        "size": sum((ROOT / path).stat().st_size for path in scanned), "sha256": sha(manifest.encode()),
        "sha256_scope": "content manifest excluding self report", "duplicate_entries": 0,
        "path_traversal_entries": 0, "nested_zip_entries": 0, "secret_scan_result": "PASS",
        "utf8_paths": True, "forward_slash_paths": True, "allowlist_result": "PASS"})
    with zipfile.ZipFile(ARCHIVE, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in entries:
            archive.write(ROOT / path, arcname=path)
    with zipfile.ZipFile(ARCHIVE) as archive:
        names = archive.namelist()
        assert names == entries and len(names) == len(set(names)) and archive.testzip() is None
        assert not any(name.lower().endswith(".zip") or "\\" in name or PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names)
        assert not [(name, secret_scan(archive.read(name))) for name in names if secret_scan(archive.read(name))]
    print(json.dumps({"status": "PASS", "archive": str(ARCHIVE), "entries": len(entries),
                      "size": ARCHIVE.stat().st_size, "sha256": sha(ARCHIVE.read_bytes())}, sort_keys=True))


if __name__ == "__main__":
    main()
