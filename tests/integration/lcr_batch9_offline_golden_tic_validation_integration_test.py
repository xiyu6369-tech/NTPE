from __future__ import annotations

import json
from pathlib import Path
import subprocess

import core.character_memory_v2 as cm
import core.chunk_cache_v2 as cc
import core.context_scene_memory as csm
import core.controlled_provider_routing as routing
import core.lcr_offline_validation as lcr
import core.multilingual_profiles as profiles
import core.post_polish_semantic_verification as semantic
from core.translation_intelligence_corpus.offline_quality_gate import evaluate_translation_candidate
from tests.unit.test_character_memory_v2 import approved_memory
from tests.unit.test_chunk_cache_v2 import T0, T1, T2, completed, identity
from tests.unit.test_context_scene_memory import context, scene
from tests.unit.test_controlled_provider_routing import routing_input
from tests.unit.test_post_polish_semantic_verification import invariant, make_input


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "lcr_batch9"


def fixed_suite():
    entries = lcr.load_validation_corpus(FIXTURES, allowed_root=FIXTURES)
    return lcr.build_validation_suite(entries)


def test_tic_human_approved_and_historical_bad_cases_use_real_offline_gate():
    payload = json.loads((ROOT / "artifacts/tic_batch7/OFFLINE_QUALITY_GATE_FIXTURES.json").read_text(encoding="utf-8"))
    items = {x["fixture_id"]: x for x in payload["items"]}
    for case_id, expected in (("B7-SUBJECT-APPROVED", "pass"), ("B7-SUBJECT-BAD", "fail"), ("B7-LEXICAL-APPROVED", "pass"), ("B7-LEXICAL-BAD", "fail")):
        item = items[case_id]
        result = evaluate_translation_candidate(
            source_text=item["source_text"], translation_text=item["translation_text"],
            applicable_regression_ids=tuple(item["applicable_regression_ids"]), candidate_id=case_id,
        )
        assert result.gate_status == expected
        assert result.regression_safe is (expected == "pass")


def test_character_and_scene_context_are_selected_from_real_stores():
    memory_store = cm.MemoryStore()
    record = approved_memory("鄭泰義", segment="batch9-character")
    cm.add_or_merge_memory(memory_store, record, now=T1)
    selected = cm.select_prompt_eligible_memories(memory_store, character_ids=("char-1",), now=T2)
    assert selected.items and selected.items[0].value == "鄭泰義"

    context_store = scene()
    record_context = context(value="主詞仍指向先前角色", segment="batch9-context")
    csm.add_or_merge_context(context_store, record_context, now=T1)
    context_selected = csm.select_context_for_translation(context_store, chapter_id="chapter-1", scene_id="scene-1", sequence_index=1, now=T2)
    assert any(x.value == "主詞仍指向先前角色" for x in context_selected.selected_records)


def test_chunk_cache_reuses_eight_and_retries_timeout_and_missing():
    store = cc.ChunkCacheStore()
    identities = tuple(identity(index=i) for i in range(10))
    resume = {}
    for index in range(8):
        _, entry = completed(store=store, index=index)
        resume[index] = {"document_id": "doc-1", "chunk_index": index, "status": "completed", "translation_hash": entry.translation_hash, "prompt_hash": entry.prompt_hash}
    timeout_entry = cc.create_cache_entry(identities[8], created_at=T0)
    cc.add_cache_entry(store, timeout_entry)
    cc.record_cache_failure(store, timeout_entry.cache_entry_id, status="timeout", failure_type="temporary", attempt_count=1, failure_ttl=60, retry_after=T2, evidence=({"kind": "diagnostic"},), updated_at=T1)
    plan = cc.plan_chunk_reexecution(identities, store, resume_state=resume, current_time=T2)
    assert plan.reusable_chunks == tuple(range(8))
    assert plan.retry_chunks == (8, 9)
    assert not plan.invalid_chunks and not plan.conflicts


def test_semantic_multilingual_and_provider_routing_boundaries_are_real():
    subject_change = semantic.verify_post_polish_semantics(
        make_input(), invariants=(invariant("subject_identity", {"expected_value": "A", "polish_value": "B"}),),
    )
    assert subject_change.status is semantic.VerificationStatus.FAILED
    assert subject_change.decision is semantic.VerificationDecision.ROLLBACK_TO_DRAFT
    assert semantic.verify_post_polish_semantics(make_input()).status is semantic.VerificationStatus.PASSED

    profile = profiles.select_language_profile("ko", "zh-Hant")
    assert profile.status == "selected" and profile.profile.profile_id == "literary-ko-zh-hant"

    route_input = routing_input(
        verified_draft_available=True, draft_required=False,
        provider_failure_history=(), cache_availability=False,
    )
    decision = routing.select_provider_route(route_input, routing.PROVIDER_PROFILES)
    plan = routing.build_provider_execution_plan(route_input, decision, routing.NVIDIA_PROFILE)
    assert plan.prepare_only and not plan.executed and plan.network_requests == 0


def test_full_fixed_suite_is_ready_only_for_batch10_planning_and_deterministic():
    item = fixed_suite()
    reports = tuple(lcr.build_validation_report(item, lcr.run_validation_suite(item)) for _ in range(3))
    assert reports[0] == reports[1] == reports[2]
    report = reports[0]
    gate = lcr.evaluate_lcr_offline_readiness(
        report, all_required_scenarios_present=set(x.scenario_type for x in item.scenarios) == set(lcr.SCENARIO_TYPES),
        production_boundaries_unchanged=True, all_regressions_pass=True, determinism_pass=True,
    )
    assert report.metrics.total_scenarios == 48 and report.metrics.passed_scenarios == 48
    assert report.metrics.false_positive_count == report.metrics.false_negative_count == 0
    assert report.metrics.provider_requests_executed == 0
    assert gate.status == "ready" and gate.meaning == "ready for Batch 10 controlled integration planning only"


def test_batch9_production_and_frozen_core_allowlist():
    lines = subprocess.run(["git", "status", "--short"], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
    allowed = (
        "core/lcr_offline_validation/", "tests/unit/test_lcr_offline_validation.py",
        "tests/integration/lcr_batch9_offline_golden_tic_validation_integration_test.py",
        "tests/fixtures/lcr_batch9/", "ntpe_lcr_batch9_offline_golden_tic_validation_test.py",
        "audits/legacy_capability_recovery/batch9/", "NTPE_LCR_BATCH9_AUDIT.zip",
    )
    assert all(line[3:].replace("\\", "/").strip('"').startswith(allowed) for line in lines)
