from __future__ import annotations

import subprocess
from pathlib import Path

import core.character_memory_v2 as character
import core.chunk_cache_v2 as cache
import core.context_scene_memory as context
import core.controlled_provider_routing as routing
import core.dual_pass_translation as dual_pass
import core.lcr_offline_validation as batch9
import core.lcr_production_shadow as shadow
import core.multilingual_profiles as multilingual
import core.post_polish_semantic_verification as semantic
from tests.unit.test_lcr_production_shadow import FLAGS_ON, shadow_input


ROOT = Path(__file__).resolve().parents[2]


def test_batch2_through_batch9_modules_are_importable_without_runtime_hook():
    modules = (character, context, cache, dual_pass, semantic, multilingual, routing, batch9)
    assert all(module.__name__.startswith("core.") for module in modules)
    assert not hasattr(shadow, "execute_provider")
    assert not hasattr(shadow, "write_resume")
    assert not hasattr(shadow, "assemble_output")


def test_production_metadata_is_immutable_and_provider_route_is_prepare_only():
    metadata = {"provider_identity": "batch8-route", "model_identity": "offline", "prepare_only": True}
    before = shadow.deterministic_fingerprint(metadata)
    view = shadow.adapt_provider_metadata(metadata)
    result = shadow.run_lcr_production_shadow(shadow_input(), flags=FLAGS_ON)
    assert view.payload["prepare_only"] is True
    assert shadow.deterministic_fingerprint(metadata) == before
    assert result.provider_route_view["prepare_only"] is True
    assert result.provider_route_view["executed"] is False
    assert result.provider_route_view["network_requests"] == 0


def test_kill_switch_activation_gate_and_baseline_boundary():
    blocked = shadow.run_lcr_production_shadow(shadow_input(), flags={**FLAGS_ON, shadow.KILL_SWITCH: True})
    assert blocked.readiness_result == "blocked"
    assert not blocked.baseline_changed and not blocked.production_output_changed
    gate = shadow.evaluate_activation_gate({
        "batch9_ready": True, "all_lcr_regressions_pass": True,
        "production_boundary_unchanged": True, "shadow_deterministic": True,
        "shadow_exceptions_isolated": True, "provider_requests_zero": True,
        "prompt_budget_within_limit": True, "request_cost_within_policy": True,
        "kill_switch_verified": True, "rollback_verified": True,
        "security_scan_pass": True, "manual_approval_present": True,
    })
    assert gate.status == "ready_for_shadow_hook"
    assert gate.active_production_authorized is False


def test_git_changes_are_batch10_allowlisted_and_production_boundaries_unchanged():
    output = subprocess.run(["git", "status", "--short"], cwd=ROOT, check=True, capture_output=True,
                            text=True, encoding="utf-8").stdout.splitlines()
    allowed = (
        "core/lcr_production_shadow/", "tests/unit/test_lcr_production_shadow.py",
        "tests/integration/lcr_batch10_production_shadow_planning_integration_test.py",
        "tests/fixtures/lcr_batch10/", "ntpe_lcr_batch10_production_shadow_planning_test.py",
        "audits/legacy_capability_recovery/batch10/", "NTPE_LCR_BATCH10_AUDIT.zip",
    )
    assert all(line[3:].replace("\\", "/").strip('"').startswith(allowed) for line in output)
