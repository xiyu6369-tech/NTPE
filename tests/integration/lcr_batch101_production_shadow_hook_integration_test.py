from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

import lts.txt_translation_runtime as runtime
import core.adaptive_context_runtime_shadow.hook as production_hook
import core.lcr_production_shadow_hook as lcr
import core.lcr_production_shadow_hook.hook as hook_module


ROOT = Path(__file__).resolve().parents[2]


def options(tmp_path: Path):
    source = tmp_path / "fixture.txt"
    source.write_text("synthetic source", encoding="utf-8")
    return runtime.TxtTranslationOptions(source, tmp_path / "output", source_language="ja", target_language="zh-Hant", dry_run=True)


def build(tmp_path: Path):
    return runtime.build_prompt_package(
        options=options(tmp_path), chunk_text="synthetic metadata-only fixture", chunk_index=1,
        chunk_total=1, locked_dictionary={}, previous_context="",
    )


def canonical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()


def test_single_production_hook_is_after_package_prepared_and_default_off(monkeypatch, tmp_path):
    monkeypatch.delenv("LCR_SHADOW_ENABLED", raising=False)
    monkeypatch.delenv("LCR_KILL_SWITCH", raising=False)
    production_hook.uninstall_txt_runtime_shadow_hook()
    baseline = build(tmp_path)
    assert production_hook.install_txt_runtime_shadow_hook()
    hooked = build(tmp_path)
    assert canonical(hooked) == canonical(baseline)


def test_production_wrapper_calls_exactly_one_lcr_hook_and_preserves_return(monkeypatch, tmp_path):
    production_hook.uninstall_txt_runtime_shadow_hook()
    baseline = build(tmp_path)
    calls = []
    monkeypatch.setattr(production_hook, "run_read_only_lcr_shadow_hook", lambda package: calls.append(canonical(package)))
    assert production_hook.install_txt_runtime_shadow_hook()
    hooked = build(tmp_path)
    assert len(calls) == 1
    assert canonical(hooked) == canonical(baseline)


def test_production_wrapper_isolates_hook_exception(monkeypatch, tmp_path):
    production_hook.uninstall_txt_runtime_shadow_hook()
    baseline = build(tmp_path)
    def broken(package):
        raise RuntimeError("synthetic hook failure")
    monkeypatch.setattr(production_hook, "run_read_only_lcr_shadow_hook", broken)
    assert production_hook.install_txt_runtime_shadow_hook()
    hooked = build(tmp_path)
    assert canonical(hooked) == canonical(baseline)


def test_enabled_hook_generates_evidence_without_provider_prompt_resume_or_output_changes(tmp_path):
    package = build(tmp_path)
    before = canonical(package)
    sink = lcr.InMemoryEvidenceSink()
    result = lcr.run_read_only_lcr_shadow_hook(
        package, feature_flags={"LCR_SHADOW_ENABLED": True, "LCR_KILL_SWITCH": False}, evidence_sink=sink
    )
    assert result.status == "completed" and canonical(package) == before
    assert len(sink.records) == 1
    record = sink.records[0]
    assert record.modules_evaluated == ("chunk_cache", "multilingual_profile", "provider_routing")
    assert record.provider_requests_executed == 0
    assert not record.production_output_changed and not record.baseline_changed


def test_production_wrapper_returns_while_real_runner_is_blocked(monkeypatch, tmp_path):
    assert lcr.wait_for_shadow_idle(1.0)
    original = hook_module.run_lcr_production_shadow

    def blocking(*args, **kwargs):
        time.sleep(0.2)
        return original(*args, **kwargs)

    monkeypatch.setenv("LCR_SHADOW_ENABLED", "true")
    monkeypatch.setenv("LCR_KILL_SWITCH", "false")
    monkeypatch.setattr(hook_module, "run_lcr_production_shadow", blocking)
    production_hook.uninstall_txt_runtime_shadow_hook()
    assert production_hook.install_txt_runtime_shadow_hook()
    started = time.perf_counter()
    result = build(tmp_path)
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert elapsed_ms < 50
    assert result["package_id"].startswith("TXT_")
    assert lcr.wait_for_shadow_idle(1.0)


def test_production_diff_is_one_file_one_hook_call_and_no_forbidden_direct_lcr_imports():
    diff = subprocess.run(["git", "diff", "--", "core/adaptive_context_runtime_shadow/hook.py"], cwd=ROOT,
                          check=True, capture_output=True, text=True, encoding="utf-8").stdout
    assert diff.count("+from core.lcr_production_shadow_hook import run_read_only_lcr_shadow_hook") == 1
    assert diff.count("+            run_read_only_lcr_shadow_hook(package)") == 1
    assert not any(name in diff for name in (
        "core.character_memory_v2", "core.context_scene_memory", "core.chunk_cache_v2",
        "core.dual_pass_translation", "core.post_polish_semantic_verification",
        "core.multilingual_profiles", "core.controlled_provider_routing",
    ))


def test_batch101_worktree_allowlist_and_no_tracked_deletions():
    lines = subprocess.run(["git", "status", "--short"], cwd=ROOT, check=True, capture_output=True,
                           text=True, encoding="utf-8").stdout.splitlines()
    allowed = (
        "core/adaptive_context_runtime_shadow/hook.py", "core/lcr_production_shadow_hook/",
        "tests/unit/test_lcr_production_shadow_hook.py",
        "tests/integration/lcr_batch101_production_shadow_hook_integration_test.py",
        "tests/fixtures/lcr_batch101/", "ntpe_lcr_batch101_production_shadow_hook_test.py",
        "audits/legacy_capability_recovery/batch10_1/", "NTPE_LCR_BATCH101_AUDIT.zip",
    )
    assert all(line[3:].replace("\\", "/").strip('"').startswith(allowed) for line in lines)
    deleted = subprocess.run(["git", "ls-files", "--deleted"], cwd=ROOT, check=True, capture_output=True,
                             text=True, encoding="utf-8").stdout.strip()
    assert deleted == ""
