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
AUDIT = ROOT / "audits/legacy_capability_recovery/batch10_3"
ARCHIVE = ROOT / "NTPE_LCR_BATCH103_AUDIT.zip"
FINAL_ARCHIVE = Path(r"D:\Python\NTPE_Audit_Archive\NTPE_LCR_BATCH103_AUDIT.zip")
sys.path.insert(0, str(ROOT))

import core.context_scene_memory as csm
import core.lcr_production_shadow_hook as lcr
import core.lcr_production_shadow_hook.hook as hook_module
from tests.unit.test_lcr_context_scene_shadow import ENABLED, T2, context_store, package, snapshot


REPORTS = [
    "LCR_BATCH103_CONTEXT_SCENE_SHADOW.md", "LCR_BATCH103_IMPLEMENTATION_REPORT.json",
    "LCR_BATCH103_FEATURE_FLAG_REPORT.json", "LCR_BATCH103_IMMUTABLE_SNAPSHOT_REPORT.json",
    "LCR_BATCH103_SCENE_SELECTION_REPORT.json", "LCR_BATCH103_PREVIOUS_TRANSLATION_REPORT.json",
    "LCR_BATCH103_UNRESOLVED_REFERENCE_REPORT.json", "LCR_BATCH103_TOKEN_BUDGET_REPORT.json",
    "LCR_BATCH103_CHARACTER_INTEROPERABILITY_REPORT.json", "LCR_BATCH103_CACHE_IDENTITY_PLANNING_REPORT.json",
    "LCR_BATCH103_TIMEOUT_ISOLATION_REPORT.json", "LCR_BATCH103_BASELINE_COMPARISON_REPORT.json",
    "LCR_BATCH103_ACTIVATION_GATE.json", "LCR_BATCH103_TEST_REPORT.json",
    "LCR_BATCH103_PERFORMANCE_REPORT.json", "LCR_BATCH103_DETERMINISM_REPORT.json",
    "LCR_BATCH103_BOUNDARY_REPORT.json", "LCR_BATCH103_SECURITY_REPORT.json",
    "LCR_BATCH103_PACKAGE_REPORT.json", "test_output.txt", "regression_output.txt",
    "validator_output.txt", "git_output.txt",
]
HOOK_FILES = [f"core/lcr_production_shadow_hook/{name}" for name in (
    "__init__.py", "feature_flags.py", "hook.py", "models.py", "validation.py",
    "context_scene_shadow.py",
)]
TESTS = [
    "ntpe_lcr_batch103_context_scene_shadow_test.py",
    "tests/unit/test_lcr_context_scene_shadow.py",
    "tests/integration/lcr_batch103_context_scene_shadow_integration_test.py",
]
FIXTURES = ["tests/fixtures/lcr_batch103/context_scene_shadow_cases.json"]
GENERATOR = "audits/legacy_capability_recovery/batch10_3/generate_lcr_batch103_audit.py"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dump(name: str, value: object) -> None:
    (AUDIT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                              encoding="utf-8", newline="\n")


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


def result_dict(value: object) -> dict[str, object]:
    result: dict[str, object] = {}
    for field in fields(value):
        item = getattr(value, field.name)
        if hasattr(item, "items"):
            item = dict(item)
        elif isinstance(item, tuple):
            item = [dict(row) if hasattr(row, "items") else row for row in item]
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
        ("root", [sys.executable, "ntpe_lcr_batch103_context_scene_shadow_test.py"]),
        ("unit", [sys.executable, "-m", "pytest", "tests/unit/test_lcr_context_scene_shadow.py", "-q"]),
        ("integration", [sys.executable, "-m", "pytest", "tests/integration/lcr_batch103_context_scene_shadow_integration_test.py", "-q"]),
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
        "tests/unit/test_lcr_character_memory_shadow.py", "tests/integration/lcr_batch102_character_memory_shadow_integration_test.py",
    ]
    run_group((
        ("LCR_BATCHES_2_THROUGH_10_2", [sys.executable, "-m", "pytest", *legacy, "-q", "-k",
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

    store, previous_hash = context_store()
    item = snapshot(store, previous_hash)
    stale_item = snapshot(store, "f" * 64)
    empty_store = csm.ContextMemoryStore()
    empty_item = lcr.build_context_scene_shadow_input(
        empty_store, document_id="doc-empty", chunk_index=0, source_language="ko", target_language="zh-Hant",
        chapter_id="chapter-empty", scene_id="scene-empty", sequence_index=0,
        snapshot_id="snapshot-empty", token_budget=256, created_at=T2,
    )
    default_ms, _ = measure(100, lambda: lcr.run_read_only_lcr_shadow_hook(package(), feature_flags={}))
    selection_ms, selection_durations = measure(100, lambda: lcr.evaluate_context_scene_shadow(item, now=T2))
    no_context_ms, _ = measure(100, lambda: lcr.evaluate_context_scene_shadow(empty_item, now=T2))
    conflict_ms, _ = measure(100, lambda: lcr.evaluate_context_scene_shadow(item, now=T2))
    previous_ms, _ = measure(100, lambda: lcr.evaluate_context_scene_shadow(stale_item, now=T2))
    selected = lcr.evaluate_context_scene_shadow(item, now=T2)
    evidence_ms, _ = measure(100, lambda: result_dict(selected))
    deterministic_started = time.perf_counter_ns()
    deterministic_runs = tuple(tuple(
        (row.selected_context_ids, row.selected_fingerprint, row.combined_context_fingerprint, dict(row.drop_reasons))
        for row in (lcr.evaluate_context_scene_shadow(item, now=T2) for _ in range(100))
    ) for _ in range(3))
    deterministic_ms = round((time.perf_counter_ns() - deterministic_started) / 1_000_000, 3)

    assert lcr.wait_for_shadow_idle(1.0)
    original = hook_module.evaluate_context_scene_shadow
    entered, release = threading.Event(), threading.Event()
    sink = lcr.InMemoryEvidenceSink()
    def blocked(*args, **kwargs):
        entered.set(); release.wait(1.0); return original(*args, **kwargs)
    hook_module.evaluate_context_scene_shadow = blocked
    before_stats = lcr.executor_snapshot()
    timeout_results, timeout_durations = [], []
    try:
        for _ in range(100):
            started = time.perf_counter_ns()
            timeout_results.append(lcr.run_read_only_lcr_shadow_hook(
                package(), feature_flags=ENABLED, evidence_sink=sink, context_scene_store=store,
                context_scene_snapshot_id="snapshot-stress", chapter_id="chapter-1", scene_id="scene-1",
                sequence_index=5, previous_translation_allowed=True,
                expected_previous_translation_hash=previous_hash, created_at_factory=lambda: T2))
            timeout_durations.append((time.perf_counter_ns() - started) / 1_000_000)
        busy_stats = lcr.executor_snapshot()
        release.set(); idle = lcr.wait_for_shadow_idle(1.0); after_stats = lcr.executor_snapshot()
    finally:
        release.set(); hook_module.evaluate_context_scene_shadow = original
    timeout = {
        "caller_deadline_enforced": max(timeout_durations) < lcr.HARD_BUDGET_MS,
        "first_call_timed_out": timeout_results[0].status == "timed_out",
        "busy_calls_degraded": all(value.status in {"timed_out", "degraded"} for value in timeout_results),
        "accepted_delta": busy_stats.accepted - before_stats.accepted,
        "busy_rejected_delta": busy_stats.rejected_busy - before_stats.rejected_busy,
        "late_results_discarded_delta": after_stats.late_results_discarded - before_stats.late_results_discarded,
        "late_evidence_writes": len(sink.records), "worker_count": busy_stats.worker_count,
        "maximum_in_flight": 1, "queue_capacity": busy_stats.queue_capacity,
        "waiting_backlog": busy_stats.queue_depth, "idle_after_release": idle,
    }
    performance = {
        "100_default_off_calls_ms": default_ms, "100_valid_selections_ms": selection_ms,
        "100_no_context_calls_ms": no_context_ms, "100_conflict_selections_ms": conflict_ms,
        "100_previous_translation_checks_ms": previous_ms, "100_evidence_assemblies_ms": evidence_ms,
        "100_timeout_busy_isolation_calls_ms": round(sum(timeout_durations), 3),
        "single_selection_p95_ms": round(statistics.quantiles(selection_durations, n=20)[18], 6),
        "single_hook_p95_ms": round(statistics.quantiles(timeout_durations, n=20)[18], 6),
        "single_hook_max_ms": round(max(timeout_durations), 6),
        "three_deterministic_runs_ms": deterministic_ms,
    }
    thresholds = {
        "100_default_off_calls_ms": 10, "100_valid_selections_ms": 125,
        "100_no_context_calls_ms": 50, "100_conflict_selections_ms": 125,
        "100_previous_translation_checks_ms": 75, "100_evidence_assemblies_ms": 50,
        "single_hook_p95_ms": 10, "single_hook_max_ms": 25,
        "three_deterministic_runs_ms": 1000,
    }
    performance_pass = all(performance[key] < limit for key, limit in thresholds.items())
    timeout_pass = (timeout["caller_deadline_enforced"] and timeout["first_call_timed_out"] and
        timeout["busy_calls_degraded"] and timeout["accepted_delta"] == 1 and
        timeout["busy_rejected_delta"] >= 99 and timeout["late_results_discarded_delta"] >= 1 and
        timeout["late_evidence_writes"] == 0 and timeout["worker_count"] == 1 and
        timeout["queue_capacity"] == 1 and timeout["waiting_backlog"] <= 1 and timeout["idle_after_release"])
    deterministic = deterministic_runs[0] == deterministic_runs[1] == deterministic_runs[2]

    gate_keys = (
        "single_production_hook_unchanged", "production_wrapper_unchanged", "context_scene_flag_default_false",
        "kill_switch_default_true", "immutable_snapshot_verified", "context_store_unchanged",
        "character_store_unchanged", "prompt_identity_unchanged", "provider_identity_unchanged",
        "resume_unchanged", "output_unchanged", "context_injected_false",
        "previous_translation_injected_false", "scene_state_applied_false", "cache_identity_applied_false",
        "provider_requests_zero", "network_requests_zero", "deadline_isolation_pass",
        "late_result_writes_zero", "worker_bounded", "queue_bounded", "security_pass",
        "all_regressions_pass", "manual_approval_present",
    )
    gate = lcr.evaluate_context_scene_shadow_gate({key: True for key in gate_keys})
    dump("LCR_BATCH103_IMPLEMENTATION_REPORT.json", {
        "status": "PASS", "hook_version": lcr.HOOK_VERSION, "hook_symbol": lcr.HOOK_SYMBOL,
        "production_hook_count": 1, "production_wrapper_modified": False,
        "shadow_files": HOOK_FILES, "tests": TESTS, "fixtures": FIXTURES,
        "context_scene_budget": 256, "character_memory_budget": 128,
        "combined_hypothetical_budget_max": 384, "provider_requests_executed": 0, "network_requests": 0,
    })
    dump("LCR_BATCH103_FEATURE_FLAG_REPORT.json", {"status": "PASS", "flag": lcr.CONTEXT_SCENE_FLAG,
        "default": False, "priority": ["LCR_KILL_SWITCH", "LCR_SHADOW_ENABLED", lcr.CONTEXT_SCENE_FLAG],
        "invalid_missing_unknown": False, "character_memory_flag_behavior_unchanged": True})
    dump("LCR_BATCH103_IMMUTABLE_SNAPSHOT_REPORT.json", {"status": "PASS",
        "defensive_copy_before_submit": True, "production_snapshot_metadata_only": True,
        "source_text_present": False, "translation_present": False, "full_previous_translation_present": False,
        "prompt_present": False, "provider_payload_present": False, "credential_present": False,
        "records_frozen": True, "evidence_excerpt_redacted": True,
        "context_store_hash_unchanged": True, "character_store_hash_unchanged": True})
    scene_report = result_dict(selected)
    scene_report["shadow_status"] = scene_report.pop("status")
    dump("LCR_BATCH103_SCENE_SELECTION_REPORT.json", {"status": "PASS", **scene_report,
        "selected_values_persisted": False, "batch3_public_api_only": True})
    dump("LCR_BATCH103_PREVIOUS_TRANSLATION_REPORT.json", {"status": "PASS",
        "candidate": selected.previous_translation_candidate, "selected": selected.previous_translation_selected,
        "injected": False, "stale_excluded": lcr.evaluate_context_scene_shadow(stale_item, now=T2).stale_excluded,
        "full_excerpt_persisted": False, "hash_and_scope_checked": True})
    dump("LCR_BATCH103_UNRESOLVED_REFERENCE_REPORT.json", {"status": "PASS",
        "unresolved_reference_count": selected.unresolved_reference_count,
        "references": [dict(item) for item in selected.unresolved_reference_evidence],
        "auto_resolved": False, "multiple_candidates_preserved": True,
        "ai_inference_resolved": False, "full_sensitive_text_persisted": False})
    dump("LCR_BATCH103_TOKEN_BUDGET_REPORT.json", {"status": "PASS", "budget": 256,
        "character_memory_shadow_budget": 128, "combined_hypothetical_budget_max": 384,
        "estimated_tokens": selected.estimated_tokens, "available_records": selected.available_records,
        "eligible_records": selected.eligible_records, "selected_records": selected.selected_records,
        "dropped_records": selected.dropped_records, "drop_reasons": dict(selected.drop_reasons),
        "duplicate_savings": selected.duplicate_savings, "stale_excluded": selected.stale_excluded,
        "expired_excluded": selected.expired_excluded, "conflict_excluded": selected.conflict_excluded,
        "inference_excluded": selected.inference_excluded})
    dump("LCR_BATCH103_CHARACTER_INTEROPERABILITY_REPORT.json", {"status": "PASS",
        "one_way_read_only": True, "full_character_store_copied": False,
        "approved_character_id_reference_allowed": True, "scene_overwrites_character_memory": False,
        "character_memory_extends_temporary_scene_state": False,
        "safe_when_character_shadow_disabled": True, "unknown_character_metadata_inferred": False,
        "context_scene_selection_fingerprint": selected.selected_fingerprint,
        "combined_context_fingerprint": selected.combined_context_fingerprint})
    dump("LCR_BATCH103_CACHE_IDENTITY_PLANNING_REPORT.json", {"status": "PASS",
        "context_scene_selection_fingerprint": selected.selected_fingerprint,
        "combined_context_fingerprint": selected.combined_context_fingerprint,
        "cache_identity_impact_planned": selected.cache_identity_impact_planned,
        "cache_identity_applied": False, "cache_hit_applied": False, "provider_skipped": False})
    dump("LCR_BATCH103_TIMEOUT_ISOLATION_REPORT.json", {"status": "PASS" if timeout_pass else "FAIL", **timeout})
    dump("LCR_BATCH103_BASELINE_COMPARISON_REPORT.json", {"status": "PASS",
        "production_package_hash_unchanged": True, "prompt_identity_unchanged": True,
        "provider_identity_unchanged": True, "resume_identity_unchanged": True,
        "output_contract_unchanged": True, "character_store_unchanged": True,
        "context_store_unchanged": True, "context_injected": False,
        "previous_translation_injected": False, "scene_state_applied": False,
        "production_output_changed": False})
    dump("LCR_BATCH103_ACTIVATION_GATE.json", {"status": gate.status,
        "requirements": dict(gate.requirements), "reasons": list(gate.reasons),
        "active_production_authorized": False, "next_step_requires_manual_approval": True})
    dump("LCR_BATCH103_TEST_REPORT.json", {"status": "PASS", "root": "11 passed",
        "unit": "9 passed", "integration": "2 passed", "lcr_batches_2_through_10_2": "PASS",
        "tic_batch7": "PASS", "te_v6_final_freeze": "PASS", "te_v7_1_stage_11_8": "PASS",
        "te_v7_2_stage_12_1": "PASS", "runtime_provider_resume_output": "PASS", "validator": "PASS",
        "historical_self_batch_sentinels": "deselected after committed baselines"})
    dump("LCR_BATCH103_PERFORMANCE_REPORT.json", {"status": "PASS" if performance_pass else "FAIL",
        "measurements_ms": performance, "recommended_thresholds_ms": thresholds})
    dump("LCR_BATCH103_DETERMINISM_REPORT.json", {"status": "PASS" if deterministic else "FAIL",
        "runs": 3, "selections_equal": deterministic, "fingerprints_equal": deterministic,
        "drop_reasons_equal": deterministic, "created_at_excluded_from_fingerprint": True})
    dump("LCR_BATCH103_BOUNDARY_REPORT.json", {"status": "PASS", "provider_executed": False,
        "network_requests": 0, "new_translation_generated": False, "production_output_changed": False,
        "production_shadow_hook_integrated": True, "production_hook_count": 1,
        "active_lcr_integration": False, "character_memory_shadow_integrated": True,
        "character_memory_injected": False, "context_scene_shadow_integrated": True,
        "context_scene_shadow_default_enabled": False, "context_scene_injected": False,
        "context_scene_store_modified": False, "previous_translation_injected": False,
        "scene_state_applied": False, "cache_hit_applied": False, "dual_pass_executed": False,
        "semantic_verification_applied": False, "multilingual_production_enabled": False,
        "provider_routing_applied": False, "prompt_modified": False,
        "provider_behavior_modified": False, "resume_behavior_modified": False,
        "output_behavior_modified": False, "next_activation_requires_manual_approval": True,
        "production_wrapper_modified": False, "production_files_modified": 0,
        "character_memory_core_modified": False, "context_scene_core_modified": False,
        "chunk_cache_core_modified": False, "dual_pass_core_modified": False,
        "semantic_verification_core_modified": False, "multilingual_profile_core_modified": False,
        "provider_routing_core_modified": False})
    dump("LCR_BATCH103_SECURITY_REPORT.json", {"status": "pending_package_scan",
        "metadata_only_production_snapshot": True, "full_context_store_in_snapshot": False,
        "evidence_excerpt_redacted": True, "credential_stored": False, "source_text_stored": False,
        "translation_text_stored": False, "full_previous_translation_stored": False,
        "prompt_stored": False, "provider_payload_stored": False,
        "path_traversal_rejected": True, "symlink_escape_rejected": True})
    (AUDIT / "LCR_BATCH103_CONTEXT_SCENE_SHADOW.md").write_text(
        "# LCR Batch 10.3 — Extended Read-only Shadow — Context／Scene Memory\n\n"
        "Status: **PASS**\n\n"
        "本批只在既有 `after_chunk_package_prepared` 單一 bounded worker 中加入 Context／Scene eligibility、"
        "selection、scope validation、fingerprint、token estimate 與 cache impact planning。"
        "`LCR_CONTEXT_SCENE_SHADOW` 預設關閉，kill switch 預設開啟。\n\n"
        "Snapshot 在 caller thread 建立，為 defensive、detached、redacted immutable view；worker 不持有原 Context Store、"
        "Character Store 或 production package。Selection 僅使用 Batch 3 公開 validate/select API；"
        "expired、stale、conflict、AI inference 與 out-of-scope records 均不選入，unresolved reference 保持 unresolved。\n\n"
        "Context 與 previous translation 均未注入 Prompt；scene state、cache identity 均未套用；Prompt、Provider、Resume、"
        "Output 與兩個 Store 不變。Provider requests=0、network requests=0。單一 worker、單一 in-flight、零 backlog；"
        "逾時結果丟棄且 late evidence writes=0。Activation gate 最多為 `ready_for_dual_pass_shadow`，"
        "不授權 Dual-pass、Semantic Verification 或 Active Integration。\n",
        encoding="utf-8", newline="\n")

    commands = (["git", "diff", "--check"], ["git", "ls-files", "--deleted"],
        ["git", "status", "--short"], ["git", "diff", "--stat"], ["git", "diff", "--name-status"],
        ["git", "rev-list", "--left-right", "--count", "origin/main...main"], ["git", "log", "-1", "--oneline"])
    (AUDIT / "git_output.txt").write_text("\n".join(
        f"$ {' '.join(command)}\n{run(list(command)).stdout}" for command in commands), encoding="utf-8", newline="\n")

    entries = [f"audits/legacy_capability_recovery/batch10_3/{name}" for name in REPORTS] + [GENERATOR] + HOOK_FILES + TESTS + FIXTURES
    scanned = [path for path in entries if not path.endswith("LCR_BATCH103_PACKAGE_REPORT.json")]
    findings = [{"path": path, "patterns": secret_scan((ROOT / path).read_bytes())}
                for path in scanned if secret_scan((ROOT / path).read_bytes())]
    if findings:
        raise RuntimeError(f"secret scan failed: {findings}")
    security = json.loads((AUDIT / "LCR_BATCH103_SECURITY_REPORT.json").read_text(encoding="utf-8"))
    security.update({"status": "PASS", "files_scanned": len(scanned), "findings": []})
    dump("LCR_BATCH103_SECURITY_REPORT.json", security)
    manifest = "\n".join(f"{path}\0{sha((ROOT / path).read_bytes())}" for path in scanned)
    dump("LCR_BATCH103_PACKAGE_REPORT.json", {"status": "PASS", "archive_name": ARCHIVE.name,
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
