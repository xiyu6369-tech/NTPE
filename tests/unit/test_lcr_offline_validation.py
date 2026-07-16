from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import core.lcr_offline_validation as lcr
import core.lcr_offline_validation.executors as executors

FIXTURES=Path(__file__).parents[1]/"fixtures"/"lcr_batch9"


def corpus():
    lcr.load_validation_corpus.cache_clear()
    return lcr.load_validation_corpus(FIXTURES,allowed_root=FIXTURES)


def suite():return lcr.build_validation_suite(corpus())


def scenario(**changes):
    values=dict(scenario_id="unit-semantic",scenario_type="semantic_mutation_case",source_case_id="unit-source",evidence_origin="synthetic",inputs={"operation":"subject"},expected_status="failed",expected_decision="rollback_to_draft",required_modules=("post_polish_semantic_verification",),protected_invariants=("subject_identity",),forbidden_outcomes=("accept_polish",),required=True,created_at="2026-07-16T00:00:00Z",version="1.0")
    values.update(changes);return lcr.create_validation_scenario(**values)


def test_registry_has_one_explicit_executor_for_every_scenario_type():
    assert set(lcr.SCENARIO_EXECUTORS)==set(lcr.SCENARIO_TYPES)
    assert all(callable(item) for item in lcr.SCENARIO_EXECUTORS.values())


def test_fixed_corpus_is_48_cases_and_contains_no_observed_or_metric_results():
    entries=corpus();assert len(entries)==48
    forbidden=lcr.FORBIDDEN_FIXTURE_RESULT_FIELDS
    for path in FIXTURES.glob("*.json"):
        value=json.loads(path.read_text(encoding="utf-8"))
        def keys(item):
            if isinstance(item,dict):
                yield from item
                for child in item.values():yield from keys(child)
            elif isinstance(item,list):
                for child in item:yield from keys(child)
        assert not forbidden.intersection(keys(value))


def test_executor_results_and_metrics_are_exact():
    item=suite();results=lcr.run_validation_suite(item);report=lcr.build_validation_report(item,results)
    assert len(results)==48 and all(x.scenario_status=="passed" for x in results)
    assert report.metrics==lcr.ValidationMetrics(48,48,0,4,1,1,15,2,2,0,0,10,2,1,0)
    assert all(x.executable_evidence for x in results if x.required)


def test_changing_expected_outcome_does_not_change_executor_observed_result():
    item=scenario();baseline=lcr.run_validation_scenario(item)
    changed=lcr.run_validation_scenario(replace(item,expected_status="passed",expected_decision="accept"))
    assert (baseline.candidate_status,baseline.decision,baseline.module_results)==(changed.candidate_status,changed.decision,changed.module_results)
    assert baseline.scenario_status=="passed" and changed.scenario_status=="failed"


@pytest.mark.parametrize("field",sorted(lcr.FORBIDDEN_FIXTURE_RESULT_FIELDS))
def test_forged_fixture_result_fields_are_schema_rejected(field):
    with pytest.raises(ValueError,match="fixture may not declare"):
        scenario(inputs={"operation":"subject",field:0 if "requests" in field else True})


def test_monkeypatched_batch6_wrong_result_makes_semantic_scenario_fail(monkeypatch):
    real=executors.semantic.verify_post_polish_semantics(executors._semantic_input())
    assert real.status is executors.semantic.VerificationStatus.PASSED
    monkeypatch.setattr(executors.semantic,"verify_post_polish_semantics",lambda *a,**k:real)
    result=lcr.run_validation_scenario(scenario())
    assert result.scenario_status=="failed"
    assert result.candidate_status in {"passed","invalid_input"}


def test_broken_cache_plan_makes_cache_scenario_fail(monkeypatch):
    item=next(x for x in suite().scenarios if x.scenario_id=="cache-ten-chunks")
    broken=SimpleNamespace(reusable_chunks=(),retry_chunks=(),invalid_chunks=(),conflicts=())
    monkeypatch.setattr(executors.cache,"plan_chunk_reexecution",lambda *a,**k:broken)
    result=lcr.run_validation_scenario(item)
    assert result.scenario_status=="failed" and result.candidate_status=="failed"


def test_missing_executor_fails_closed(monkeypatch):
    monkeypatch.delitem(lcr.SCENARIO_EXECUTORS,"semantic_mutation_case")
    result=lcr.run_validation_scenario(scenario())
    assert result.scenario_status=="failed" and not result.executable_evidence
    assert result.issues==("missing_scenario_executor",)


def test_module_exception_never_becomes_pass(monkeypatch):
    def explode(*args,**kwargs):raise RuntimeError("fixed failure")
    monkeypatch.setattr(executors.semantic,"verify_post_polish_semantics",explode)
    result=lcr.run_validation_scenario(scenario())
    assert result.scenario_status=="failed" and result.candidate_status=="invalid_input"
    assert result.issues[0].startswith("executor_exception:RuntimeError")


def test_metrics_read_executor_events_not_fixture_budget_values():
    item=suite();results=lcr.run_validation_suite(item);baseline=lcr.calculate_validation_metrics(item,results)
    altered=replace(item,scenarios=tuple(replace(x,inputs={**x.inputs,"maximum_budget":999999}) for x in item.scenarios))
    assert lcr.calculate_validation_metrics(altered,results)==baseline
    first=replace(results[0],metric_events={"provider_requests_executed":3})
    assert lcr.calculate_validation_metrics(item,(first,)+results[1:]).provider_requests_executed==3


def test_readiness_requires_all_required_executable_evidence():
    item=suite();results=lcr.run_validation_suite(item);index=next(i for i,x in enumerate(results) if x.required)
    broken=results[:index]+(replace(results[index],executable_evidence=False),)+results[index+1:]
    report=lcr.build_validation_report(item,broken)
    gate=lcr.evaluate_lcr_offline_readiness(report,all_required_scenarios_present=True,production_boundaries_unchanged=True,all_regressions_pass=True,determinism_pass=True)
    assert gate.status=="not_ready" and gate.reasons[0]=="executable_scenario_evidence_incomplete"


def test_informational_golden_insufficient_evidence_does_not_block_ready_gate():
    item=suite();results=lcr.run_validation_suite(item);golden=[x for x in results if x.scenario_id.startswith("golden-")]
    assert golden and all(not x.required and not x.executable_evidence and x.candidate_status=="insufficient_evidence" for x in golden)
    report=lcr.build_validation_report(item,results);gate=lcr.evaluate_lcr_offline_readiness(report,all_required_scenarios_present=True,production_boundaries_unchanged=True,all_regressions_pass=True,determinism_pass=True)
    assert gate.status=="ready" and gate.meaning=="ready for Batch 10 controlled integration planning only"


def test_three_runs_and_serialization_are_deterministic():
    item=suite();runs=tuple(lcr.run_validation_suite(item) for _ in range(3));assert runs[0]==runs[1]==runs[2]
    encoded=lcr.serialize_validation_suite(item);decoded=lcr.deserialize_validation_suite(encoded);assert decoded==item and lcr.serialize_validation_suite(decoded)==encoded


def test_expected_candidate_rejection_is_scenario_pass():
    result=lcr.run_validation_scenario(scenario());assert result.scenario_status=="passed" and result.candidate_status=="failed"


def test_duplicate_unknown_schema_and_invalid_type_fail_closed():
    item=scenario()
    with pytest.raises(ValueError,match="duplicate"):lcr.validate_validation_suite(lcr.ValidationSuite("1.0","1.0","x",(item,item),"a"*64))
    with pytest.raises(ValueError,match="unknown schema"):lcr.validate_validation_suite(lcr.ValidationSuite("2.0","1.0","x",(item,),"a"*64))
    with pytest.raises(ValueError):scenario(scenario_type="unknown")


def test_malformed_unsafe_and_traversal_payloads_rejected():
    with pytest.raises(ValueError,match="malformed JSON"):lcr.deserialize_validation_suite("{")
    payload=json.loads(lcr.serialize_validation_suite(suite()));payload["scenarios"][0]["inputs"]["path"]="../escape"
    with pytest.raises(ValueError,match="path traversal"):lcr.deserialize_validation_suite(json.dumps(payload))
    with pytest.raises(ValueError,match="path traversal"):lcr.load_validation_corpus(FIXTURES,allowed_root=FIXTURES/"child")


def test_symlink_escape_rejected(tmp_path):
    link=tmp_path/"fixtures-link"
    try:link.symlink_to(FIXTURES,target_is_directory=True)
    except OSError:pytest.skip("symlink creation unavailable")
    with pytest.raises(ValueError,match="symlink escape"):lcr.load_validation_corpus(link,allowed_root=tmp_path)
