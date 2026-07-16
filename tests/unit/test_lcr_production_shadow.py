from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import core.lcr_production_shadow as lcr


FLAGS_ON = {name: True for name in lcr.SHADOW_FLAGS}
FLAGS_ON[lcr.KILL_SWITCH] = False


def shadow_input(**changes):
    values = dict(
        document_id="synthetic-doc", chunk_index=0, source_hash="a" * 64,
        source_language="ja", target_language="zh-Hant", prompt_identity="prompt-v1",
        provider_identity="nvidia-prepare-only", model_identity="model-v1",
        quality_policy_identity="quality-v1", resume_identity="resume-v1",
        output_contract_identity="output-v1", baseline_context_fingerprint="b" * 64,
        baseline_glossary_fingerprint="c" * 64, runtime_version="test-runtime",
        feature_flag_state=FLAGS_ON, created_at="2026-07-16T00:00:00Z",
    )
    values.update(changes)
    return lcr.create_shadow_input(**values)


def test_inventory_and_decision_matrix_cover_required_boundaries():
    inventory = lcr.build_integration_inventory()
    assert len(inventory) == 15
    assert {x["integration_point_id"] for x in inventory} >= {
        "runtime_entry", "request_construction", "prompt_assembly", "provider_boundary",
        "retry_boundary", "resume_journal", "chunk_result", "output_assembly",
        "quality_gate", "cli_flags", "config_loading", "feature_flags",
        "observability", "cache", "release_guards",
    }
    assert all(not x["active_write_required"] for x in inventory)
    assert {x["decision"] for x in lcr.build_decision_matrix()} <= {
        "SHADOW_READ", "SHADOW_COMPUTE", "SHADOW_COMPARE", "DEFER", "BLOCKED", "NOT_RECOMMENDED"
    }


def test_defaults_fail_closed_and_kill_switch_dominates():
    assert all(not lcr.DEFAULT_FLAGS[name] for name in lcr.SHADOW_FLAGS)
    assert lcr.DEFAULT_FLAGS[lcr.KILL_SWITCH]
    invalid = lcr.resolve_feature_flags({"LCR_SHADOW_ENABLED": "maybe", lcr.KILL_SWITCH: "invalid"})
    assert invalid[lcr.KILL_SWITCH] and not invalid["LCR_SHADOW_ENABLED"]
    dominated = lcr.resolve_feature_flags({**FLAGS_ON, lcr.KILL_SWITCH: True})
    assert all(not dominated[name] for name in lcr.SHADOW_FLAGS)


@pytest.mark.parametrize("adapter,payload", [
    (lcr.adapt_runtime_metadata, {"runtime_version": "v", "document_id": "d", "chunk_index": 1, "ignored": []}),
    (lcr.adapt_prompt_identity, {"prompt_identity": "p", "context_fingerprint": "c", "glossary_fingerprint": "g"}),
    (lcr.adapt_resume_read_only, {"resume_identity": "r", "status": "complete", "attempt_count": 1}),
    (lcr.adapt_output_contract, {"output_contract_identity": "o", "format": "text", "encoding": "utf-8"}),
    (lcr.adapt_quality_evidence, {"quality_policy_identity": "q", "requires_semantic_verification": True}),
    (lcr.adapt_provider_metadata, {"provider_identity": "prepare-only", "model_identity": "m", "prepare_only": True}),
])
def test_adapters_are_defensive_and_read_only(adapter, payload):
    original = lcr.deterministic_fingerprint(payload)
    view = adapter(payload)
    assert lcr.deterministic_fingerprint(payload) == original
    assert view.source_fingerprint == original
    with pytest.raises(FrozenInstanceError):
        view.adapter = "changed"


def test_adapters_reject_sensitive_and_raw_fields():
    for field in ("api_key", "authorization_header", "raw_provider_request", "raw_provider_response", "source_text", "translation_text"):
        with pytest.raises(ValueError):
            lcr.adapt_provider_metadata({"provider_identity": "x", field: "forbidden-value"})


def test_runner_skips_blocks_completes_and_isolates_failures():
    item = shadow_input()
    skipped = lcr.run_lcr_production_shadow(item, flags={})
    blocked = lcr.run_lcr_production_shadow(item, flags={lcr.KILL_SWITCH: True})
    completed = lcr.run_lcr_production_shadow(item, flags=FLAGS_ON)
    degraded = lcr.run_lcr_production_shadow(
        item, flags=FLAGS_ON, module_overrides={"character_memory": lambda _: 1 / 0}
    )
    assert skipped.readiness_result == "blocked"  # omitted flags retain kill-switch default
    assert blocked.readiness_result == "blocked"
    assert completed.readiness_result == "completed"
    assert degraded.readiness_result == "degraded"
    for result in (skipped, blocked, completed, degraded):
        assert not result.baseline_changed and not result.production_output_changed
        assert result.provider_requests_executed == 0
        assert lcr.validate_shadow_result(result) == ()


def test_shadow_views_never_apply_or_execute():
    result = lcr.run_lcr_production_shadow(shadow_input(), flags=FLAGS_ON, module_overrides={
        "character_memory": lambda _: {"selected": True, "injected": False, "applied": False},
        "context_scene": lambda _: {"selected": True, "injected": False, "applied": False},
        "chunk_cache": lambda _: {"cache_hit_candidate": True, "cache_hit_applied": False, "applied": False},
        "dual_pass": lambda _: {"recommended": True, "executed": False, "applied": False},
        "semantic_verification": lambda _: {"required": True, "executed": False, "applied": False},
        "provider_routing": lambda _: {"prepare_only": True, "executed": False, "network_requests": 0},
    })
    assert result.character_memory_view["injected"] is False
    assert result.context_scene_view["injected"] is False
    assert result.cache_decision["cache_hit_applied"] is False
    assert result.dual_pass_decision["executed"] is False
    assert result.provider_route_view == {"prepare_only": True, "executed": False, "network_requests": 0}


def test_comparison_budget_cost_and_cache_fail_closed():
    baseline = {"planned_request_count": 1, "cache_eligibility": True}
    candidate = {"planned_request_count": 2, "prompt_additive_tokens": 769,
                 "cache_eligibility": True, "cache_identity_complete": False}
    result = lcr.compare_baseline_shadow(baseline, candidate)
    assert result.warnings == ("provider_cost_increase",)
    assert result.blocking_reasons == ("prompt_budget_exceeded", "cache_identity_incomplete")


def test_activation_gate_requires_every_condition_and_never_authorizes_active_production():
    evidence = {name: True for name in (
        "batch9_ready", "all_lcr_regressions_pass", "production_boundary_unchanged",
        "shadow_deterministic", "shadow_exceptions_isolated", "provider_requests_zero",
        "prompt_budget_within_limit", "request_cost_within_policy", "kill_switch_verified",
        "rollback_verified", "security_scan_pass", "manual_approval_present",
    )}
    assert lcr.evaluate_activation_gate({}).status == "insufficient_evidence"
    failed = lcr.evaluate_activation_gate({**evidence, "provider_requests_zero": False})
    ready = lcr.evaluate_activation_gate(evidence)
    assert failed.status == "not_ready"
    assert ready.status == "ready_for_shadow_hook" and not ready.active_production_authorized


def test_rollback_serialization_determinism_and_paths(tmp_path: Path):
    assert [step.level for step in lcr.build_rollback_plan()] == list(range(5))
    with pytest.raises(ValueError):
        lcr.build_rollback_plan(5)
    item = shadow_input()
    assert lcr.round_trip(item) == lcr.round_trip(item)
    assert lcr.deterministic_fingerprint(item) == lcr.deterministic_fingerprint(item)
    inside = tmp_path / "fixture.json"
    inside.write_text("{}", encoding="utf-8")
    assert lcr.resolve_allowed_path(inside, tmp_path) == inside.resolve()
    with pytest.raises(ValueError):
        lcr.resolve_allowed_path(tmp_path.parent / "escape.json", tmp_path)


def test_one_hundred_runs_are_deterministic():
    results = tuple(lcr.run_lcr_production_shadow(shadow_input(chunk_index=i, source_hash=f"{i:064x}"), flags=FLAGS_ON) for i in range(100))
    again = tuple(lcr.run_lcr_production_shadow(shadow_input(chunk_index=i, source_hash=f"{i:064x}"), flags=FLAGS_ON) for i in range(100))
    assert [x.deterministic_fingerprint for x in results] == [x.deterministic_fingerprint for x in again]
    assert all(x.provider_requests_executed == 0 and not x.production_output_changed for x in results)
