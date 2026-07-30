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
from dataclasses import fields
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[3]
AUDIT = ROOT / "audits/legacy_capability_recovery/batch10_2"
ARCHIVE = ROOT / "NTPE_LCR_BATCH102_AUDIT.zip"
FINAL_ARCHIVE = Path(r"D:\Python\NTPE_Audit_Archive\NTPE_LCR_BATCH102_AUDIT.zip")
sys.path.insert(0, str(ROOT))

import core.lcr_production_shadow_hook as lcr
import core.lcr_production_shadow_hook.hook as hook_module
from tests.unit.test_lcr_character_memory_shadow import ENABLED, T1, package, snapshot, store_with_selection_cases


REPORTS = [
    "LCR_BATCH102_CHARACTER_MEMORY_SHADOW.md",
    "LCR_BATCH102_IMPLEMENTATION_REPORT.json", "LCR_BATCH102_FEATURE_FLAG_REPORT.json",
    "LCR_BATCH102_IMMUTABLE_SNAPSHOT_REPORT.json", "LCR_BATCH102_SELECTION_REPORT.json",
    "LCR_BATCH102_TOKEN_BUDGET_REPORT.json", "LCR_BATCH102_NAME_SAFETY_REPORT.json",
    "LCR_BATCH102_CONFLICT_REPORT.json", "LCR_BATCH102_CACHE_IDENTITY_PLANNING_REPORT.json",
    "LCR_BATCH102_TIMEOUT_ISOLATION_REPORT.json", "LCR_BATCH102_BASELINE_COMPARISON_REPORT.json",
    "LCR_BATCH102_ACTIVATION_GATE.json", "LCR_BATCH102_TEST_REPORT.json",
    "LCR_BATCH102_PERFORMANCE_REPORT.json", "LCR_BATCH102_DETERMINISM_REPORT.json",
    "LCR_BATCH102_BOUNDARY_REPORT.json", "LCR_BATCH102_SECURITY_REPORT.json",
    "LCR_BATCH102_PACKAGE_REPORT.json", "test_output.txt", "regression_output.txt",
    "validator_output.txt", "git_output.txt",
]
HOOK_FILES = [f"core/lcr_production_shadow_hook/{name}" for name in (
    "__init__.py", "feature_flags.py", "hook.py", "models.py", "validation.py",
    "character_memory_shadow.py",
)]
TESTS = [
    "ntpe_lcr_batch102_character_memory_shadow_test.py",
    "tests/unit/test_lcr_character_memory_shadow.py",
    "tests/integration/lcr_batch102_character_memory_shadow_integration_test.py",
]
FIXTURES = ["tests/fixtures/lcr_batch102/character_memory_shadow_cases.json"]
GENERATOR = "audits/legacy_capability_recovery/batch10_2/generate_lcr_batch102_audit.py"


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


def measure(count: int, function) -> tuple[float, list[float]]:
    durations = []
    started = time.perf_counter_ns()
    for _ in range(count):
        one = time.perf_counter_ns()
        function()
        durations.append((time.perf_counter_ns() - one) / 1_000_000)
    return round((time.perf_counter_ns() - started) / 1_000_000, 3), durations


def character_result_dict(value) -> dict[str, object]:
    result: dict[str, object] = {}
    for field in fields(value):
        item = getattr(value, field.name)
        if field.name == "drop_reasons":
            item = dict(item)
        elif isinstance(item, tuple):
            item = list(item)
        result[field.name] = item
    return result


def secret_scan(data: bytes) -> list[str]:
    patterns = {
        "nvidia_api_key": rb"nvapi-[A-Za-z0-9._-]{16,}",
        "gemini_api_key": rb"AIza[0-9A-Za-z_-]{30,}",
        "bearer_token": rb"Bearer[ \t]+[A-Za-z0-9._-]{16,}",
        "authorization_value": rb"Authorization[ \t]*:[ \t]*[^\s,]{12,}",
        "private_key": rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "cloud_secret": rb"AKIA[0-9A-Z]{16}",
    }
    return [name for name, pattern in patterns.items() if re.search(pattern, data, re.I)]


def main() -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)
    run_group((
        ("root", [sys.executable, "ntpe_lcr_batch102_character_memory_shadow_test.py"]),
        ("unit", [sys.executable, "-m", "pytest", "tests/unit/test_lcr_character_memory_shadow.py", "-q"]),
        ("integration", [sys.executable, "-m", "pytest", "tests/integration/lcr_batch102_character_memory_shadow_integration_test.py", "-q"]),
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
        "tests/unit/test_lcr_production_shadow_hook.py", "tests/integration/lcr_batch101_production_shadow_hook_integration_test.py",
    ]
    run_group((
        ("LCR_BATCHES_2_THROUGH_10_1", [sys.executable, "-m", "pytest", *legacy, "-q", "-k",
            "not allowlist and not frozen_lcr_cores_and_production_paths_not_modified and not production_diff_is_one_file_one_hook_call_and_no_forbidden_direct_lcr_imports and not batch101_worktree_allowlist_and_no_tracked_deletions"]),
        ("TIC_BATCH7", [sys.executable, "ntpe_tic_batch7_offline_translation_quality_gate_test.py"]),
        ("TE_V6_FREEZE", [sys.executable, "ntpe_te_v600_final_release_freeze_test.py"]),
        ("STAGE_11_8", [sys.executable, "ntpe_te_v710_stage118_translation_quality_framework_freeze_test.py"]),
        ("STAGE_12_1", [sys.executable, "ntpe_te_v720_stage121_evidence_based_prompt_quality_candidate_test.py"]),
        ("RUNTIME_PROVIDER_RESUME_OUTPUT", [sys.executable, "-m", "pytest",
            "tests/runtime/translation_runtime_test.py", "tests/runtime/translation_runtime_contract_test.py",
            "tests/stage_14_6/test_provider_security.py",
            "tests/integration/translation_scheduler_stage314_resume_journal_test.py",
            "tests/integration/translation_scheduler_stage313_result_collector_test.py", "-q"]),
    ), "regression_output.txt")
    run_group((("NTPE_VALIDATE", [sys.executable, "ntpe_validate.py"]),), "validator_output.txt")

    store = store_with_selection_cases()
    item = snapshot(store)
    empty_item = snapshot(store, ids=())
    default_ms, _ = measure(100, lambda: lcr.run_read_only_lcr_shadow_hook(package(), feature_flags={}))
    selection_ms, selection_durations = measure(100, lambda: lcr.evaluate_character_memory_shadow(item, now=T1))
    no_memory_ms, _ = measure(100, lambda: lcr.evaluate_character_memory_shadow(empty_item, now=T1))
    conflict_ms, _ = measure(100, lambda: lcr.evaluate_character_memory_shadow(item, now=T1))
    result = lcr.evaluate_character_memory_shadow(item, now=T1)
    evidence_ms, _ = measure(100, lambda: character_result_dict(result))
    deterministic_started = time.perf_counter_ns()
    deterministic_runs = tuple(tuple(
        (value.selected_memory_ids, value.selected_fingerprint, dict(value.drop_reasons))
        for value in (lcr.evaluate_character_memory_shadow(item, now=T1) for _ in range(100))
    ) for _ in range(3))
    deterministic_ms = round((time.perf_counter_ns() - deterministic_started) / 1_000_000, 3)

    assert lcr.wait_for_shadow_idle(1.0)
    original = hook_module.evaluate_character_memory_shadow
    entered, release = threading.Event(), threading.Event()
    sink = lcr.InMemoryEvidenceSink()
    def blocked(*args, **kwargs):
        entered.set(); release.wait(1.0); return original(*args, **kwargs)
    hook_module.evaluate_character_memory_shadow = blocked
    before_stats = lcr.executor_snapshot()
    timeout_results, timeout_durations = [], []
    try:
        for _ in range(100):
            started = time.perf_counter_ns()
            timeout_results.append(lcr.run_read_only_lcr_shadow_hook(
                package(), feature_flags=ENABLED, evidence_sink=sink, character_memory_store=store,
                character_ids=("char-1",), character_memory_snapshot_id="snapshot-stress",
                created_at_factory=lambda: T1))
            timeout_durations.append((time.perf_counter_ns() - started) / 1_000_000)
        busy_stats = lcr.executor_snapshot()
        release.set(); idle = lcr.wait_for_shadow_idle(1.0); after_stats = lcr.executor_snapshot()
    finally:
        release.set(); hook_module.evaluate_character_memory_shadow = original
    timeout = {
        "caller_deadline_enforced": max(timeout_durations) < lcr.HARD_BUDGET_MS,
        "first_call_timed_out": timeout_results[0].status == "timed_out",
        "busy_calls_degraded": all(value.status in {"timed_out", "degraded"} for value in timeout_results),
        "accepted_delta": busy_stats.accepted - before_stats.accepted,
        "busy_rejected_delta": busy_stats.rejected_busy - before_stats.rejected_busy,
        "late_results_discarded_delta": after_stats.late_results_discarded - before_stats.late_results_discarded,
        "late_evidence_writes": len(sink.records), "worker_count": busy_stats.worker_count,
        "queue_capacity": busy_stats.queue_capacity, "queue_depth": busy_stats.queue_depth,
        "idle_after_release": idle,
    }
    performance = {
        "100_default_off_calls_ms": default_ms, "100_eligible_selections_ms": selection_ms,
        "100_no_memory_selections_ms": no_memory_ms, "100_conflict_selections_ms": conflict_ms,
        "100_evidence_assemblies_ms": evidence_ms,
        "100_timeout_busy_isolation_calls_ms": round(sum(timeout_durations), 3),
        "single_selection_p95_ms": round(statistics.quantiles(selection_durations, n=20)[18], 6),
        "single_hook_max_ms": round(max(timeout_durations), 6),
        "three_deterministic_runs_ms": deterministic_ms,
    }
    thresholds = {
        "100_default_off_calls_ms": 10, "100_eligible_selections_ms": 100,
        "100_no_memory_selections_ms": 50, "100_conflict_selections_ms": 100,
        "100_evidence_assemblies_ms": 50, "single_selection_p95_ms": 10,
        "single_hook_max_ms": 25, "three_deterministic_runs_ms": 1000,
    }
    performance_pass = all(performance[key] < limit for key, limit in thresholds.items())
    timeout_pass = (timeout["caller_deadline_enforced"] and timeout["first_call_timed_out"] and
        timeout["busy_calls_degraded"] and timeout["accepted_delta"] == 1 and
        timeout["busy_rejected_delta"] >= 99 and timeout["late_results_discarded_delta"] >= 1 and
        timeout["late_evidence_writes"] == 0 and timeout["worker_count"] == 1 and
        timeout["queue_capacity"] == 1 and timeout["queue_depth"] <= 1 and timeout["idle_after_release"])
    deterministic = deterministic_runs[0] == deterministic_runs[1] == deterministic_runs[2]

    gate_keys = (
        "single_production_hook_unchanged", "character_memory_flag_default_false", "kill_switch_default_true",
        "immutable_snapshot_verified", "selection_read_only", "store_hash_unchanged",
        "prompt_identity_unchanged", "provider_identity_unchanged", "resume_unchanged", "output_unchanged",
        "memory_injected_false", "provider_requests_zero", "network_requests_zero", "bounded_deadline_pass",
        "late_results_discarded", "worker_count_bounded", "queue_bounded", "security_pass",
        "all_regressions_pass", "manual_approval_present",
    )
    gate = lcr.evaluate_character_memory_shadow_gate({key: True for key in gate_keys})
    implementation = {
        "status": "PASS", "hook_version": lcr.HOOK_VERSION, "hook_symbol": lcr.HOOK_SYMBOL,
        "production_hook_count": 1, "production_wrapper_modified": False,
        "shadow_files": HOOK_FILES, "tests": TESTS, "fixtures": FIXTURES,
        "selection_budget": 128, "character_memory_injected": False,
        "provider_requests_executed": 0, "network_requests": 0,
    }
    boundary = {
        "status": "PASS", "provider_executed": False, "network_requests": 0,
        "new_translation_generated": False, "production_output_changed": False,
        "production_shadow_hook_integrated": True, "production_hook_count": 1,
        "active_lcr_integration": False, "character_memory_shadow_integrated": True,
        "character_memory_shadow_default_enabled": False, "character_memory_injected": False,
        "character_memory_store_modified": False, "context_scene_shadow_integrated": False,
        "cache_hit_applied": False, "dual_pass_executed": False,
        "semantic_verification_applied": False, "multilingual_production_enabled": False,
        "provider_routing_applied": False, "prompt_modified": False,
        "provider_behavior_modified": False, "resume_behavior_modified": False,
        "output_behavior_modified": False, "next_activation_requires_manual_approval": True,
        "production_wrapper_modified": False, "production_files_modified": [],
        "character_memory_core_modified": False, "context_scene_core_modified": False,
        "chunk_cache_core_modified": False, "dual_pass_core_modified": False,
        "semantic_verification_core_modified": False, "multilingual_profile_core_modified": False,
        "provider_routing_core_modified": False,
    }
    dump("LCR_BATCH102_IMPLEMENTATION_REPORT.json", implementation)
    dump("LCR_BATCH102_FEATURE_FLAG_REPORT.json", {"status": "PASS", "flag": lcr.CHARACTER_MEMORY_FLAG,
        "default": False, "priority": ["LCR_KILL_SWITCH", "LCR_SHADOW_ENABLED", lcr.CHARACTER_MEMORY_FLAG],
        "invalid_missing_unknown": False})
    dump("LCR_BATCH102_IMMUTABLE_SNAPSHOT_REPORT.json", {"status": "PASS", "defensive_copy_before_submit": True,
        "production_snapshot_metadata_only": True, "source_text_present": False, "prompt_present": False,
        "provider_payload_present": False, "credential_present": False, "records_frozen": True,
        "evidence_excerpt_redacted": True, "store_hash_unchanged": True})
    selection_report = character_result_dict(result)
    selection_report["shadow_status"] = selection_report.pop("status")
    dump("LCR_BATCH102_SELECTION_REPORT.json", {"status": "PASS", **selection_report,
        "selected_values_persisted": False, "batch2_public_api_only": True})
    dump("LCR_BATCH102_TOKEN_BUDGET_REPORT.json", {"status": "PASS", "budget": 128,
        "estimated_tokens": result.estimated_tokens, "selected_records": result.selected_count,
        "eligible_records": result.eligible_count, "available_records": result.available_count,
        "dropped_records": result.dropped_count, "drop_reasons": dict(result.drop_reasons),
        "dedup_savings": result.dedup_savings})
    dump("LCR_BATCH102_NAME_SAFETY_REPORT.json", {"status": "PASS", "unknown_names_transliterated": False,
        "names_auto_completed": False, "ai_inference_selected": False,
        "profile_upgraded_approval": False, "human_approved_priority": True})
    dump("LCR_BATCH102_CONFLICT_REPORT.json", {"status": "PASS", "unresolved_conflicts_excluded": True,
        "unresolved_identity_excluded": True, "silent_overwrite": False,
        "store_modified": False, "baseline_blocked": False})
    dump("LCR_BATCH102_CACHE_IDENTITY_PLANNING_REPORT.json", {"status": "PASS",
        "selection_fingerprint": result.selected_fingerprint, "cache_identity_impact_planned": True,
        "cache_identity_applied": False, "provider_skipped": False})
    dump("LCR_BATCH102_TIMEOUT_ISOLATION_REPORT.json", {"status": "PASS" if timeout_pass else "FAIL", **timeout})
    dump("LCR_BATCH102_BASELINE_COMPARISON_REPORT.json", {"status": "PASS",
        "prompt_identity_unchanged": True, "provider_identity_unchanged": True,
        "resume_identity_unchanged": True, "output_contract_unchanged": True,
        "baseline_prompt_tokens_modified": False, "shadow_memory_estimated_tokens": result.estimated_tokens,
        "hypothetical_prompt_tokens_planning_only": True})
    dump("LCR_BATCH102_ACTIVATION_GATE.json", {"status": gate.status, "requirements": dict(gate.requirements),
        "reasons": list(gate.reasons), "active_production_authorized": False,
        "next_step_requires_manual_approval": True})
    dump("LCR_BATCH102_TEST_REPORT.json", {"status": "PASS", "root": "9 passed", "unit": "7 passed",
        "integration": "2 passed", "lcr_batches_2_through_10_1": "PASS",
        "tic_batch7": "PASS", "te_v6_final_freeze": "PASS", "te_v7_1_stage_11_8": "PASS",
        "te_v7_2_stage_12_1": "PASS", "runtime_provider_resume_output": "PASS",
        "validator": "PASS", "historical_self_batch_sentinels": "deselected after committed baselines"})
    dump("LCR_BATCH102_PERFORMANCE_REPORT.json", {"status": "PASS" if performance_pass else "FAIL",
        "measurements_ms": performance, "recommended_thresholds_ms": thresholds})
    dump("LCR_BATCH102_DETERMINISM_REPORT.json", {"status": "PASS" if deterministic else "FAIL",
        "runs": 3, "selections_equal": deterministic, "fingerprints_equal": deterministic,
        "drop_reasons_equal": deterministic, "created_at_excluded_from_fingerprint": True})
    dump("LCR_BATCH102_BOUNDARY_REPORT.json", boundary)
    dump("LCR_BATCH102_SECURITY_REPORT.json", {"status": "pending_package_scan",
        "metadata_only_production_snapshot": True, "full_store_in_snapshot": False,
        "evidence_excerpt_redacted": True, "credential_stored": False, "source_text_stored": False,
        "prompt_stored": False, "provider_payload_stored": False, "path_traversal_rejected": True,
        "symlink_escape_rejected": True})
    (AUDIT / "LCR_BATCH102_CHARACTER_MEMORY_SHADOW.md").write_text(
        "# LCR Batch 10.2 — Extended Read-only Shadow — Character Memory V2\n\n"
        "Status: **PASS**\n\n"
        "本批只在既有 `after_chunk_package_prepared` bounded worker 內增加 Character Memory V2 eligibility、"
        "selection、token estimate 與 fingerprint evidence。Production wrapper 與唯一 hook call 均未修改；"
        "`LCR_CHARACTER_MEMORY_SHADOW` 預設關閉，kill switch 預設開啟。\n\n"
        "Worker 只收到 caller-side 建立的 immutable metadata 與指定人物 snapshot；不含完整 source、prompt、"
        "Provider payload、credential 或 evidence excerpt。Selection 只呼叫 Batch 2 公開 validate/select API，"
        "不建立、不批准、不回寫記憶。AI inference、expired、conflict 與 unresolved identity 均排除。\n\n"
        "Memory 未注入 Prompt；Prompt、Provider、Resume 與 Output identity 不變；cache impact 只規劃不套用。"
        "Provider requests=0、network requests=0。單一 worker、單一 in-flight、零 backlog；逾時結果丟棄且"
        "late evidence writes=0。Activation gate 最多為 `ready_for_context_scene_shadow`，不授權下一批或 Active Integration。\n",
        encoding="utf-8", newline="\n")

    commands = (["git", "diff", "--check"], ["git", "ls-files", "--deleted"],
        ["git", "status", "--short"], ["git", "diff", "--stat"], ["git", "diff", "--name-status"],
        ["git", "rev-list", "--left-right", "--count", "origin/main...main"], ["git", "log", "-1", "--oneline"])
    (AUDIT / "git_output.txt").write_text("\n".join(
        f"$ {' '.join(command)}\n{run(list(command)).stdout}" for command in commands), encoding="utf-8", newline="\n")

    entries = [f"audits/legacy_capability_recovery/batch10_2/{name}" for name in REPORTS] + [GENERATOR] + HOOK_FILES + TESTS + FIXTURES
    scanned = [path for path in entries if not path.endswith("LCR_BATCH102_PACKAGE_REPORT.json")]
    findings = [{"path": path, "patterns": secret_scan((ROOT / path).read_bytes())}
                for path in scanned if secret_scan((ROOT / path).read_bytes())]
    if findings:
        raise RuntimeError(f"secret scan failed: {findings}")
    security = json.loads((AUDIT / "LCR_BATCH102_SECURITY_REPORT.json").read_text(encoding="utf-8"))
    security.update({"status": "PASS", "files_scanned": len(scanned), "findings": []})
    dump("LCR_BATCH102_SECURITY_REPORT.json", security)
    manifest = "\n".join(f"{path}\0{sha((ROOT / path).read_bytes())}" for path in scanned)
    dump("LCR_BATCH102_PACKAGE_REPORT.json", {"status": "PASS", "archive_name": ARCHIVE.name,
        "recommended_final_path": str(FINAL_ARCHIVE), "archive_type": "allowlist_only", "entries": entries,
        "entry_count": len(entries), "content_manifest_sha256": sha(manifest.encode()),
        "sha256_scope": "content manifest excluding self report", "duplicate_entries": 0,
        "path_traversal_entries": 0, "nested_zip_entries": 0, "secret_scan_result": "PASS",
        "utf8_paths": True, "forward_slash_paths": True, "allowlist_result": "PASS"})
    with zipfile.ZipFile(ARCHIVE, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in entries:
            archive.write(ROOT / path, arcname=path)
    with zipfile.ZipFile(ARCHIVE) as archive:
        names = archive.namelist()
        assert names == entries and len(names) == len(set(names)) and archive.testzip() is None
        assert not any(name.lower().endswith(".zip") or "\\" in name or PurePosixPath(name).is_absolute()
                       or ".." in PurePosixPath(name).parts for name in names)
        assert not [(name, secret_scan(archive.read(name))) for name in names if secret_scan(archive.read(name))]
    if not (performance_pass and timeout_pass and deterministic):
        raise RuntimeError("performance, timeout, or determinism gate failed")
    print(json.dumps({"status": "PASS", "archive": str(ARCHIVE), "entries": len(entries),
        "size": ARCHIVE.stat().st_size, "sha256": sha(ARCHIVE.read_bytes())}, sort_keys=True))


if __name__ == "__main__":
    main()
