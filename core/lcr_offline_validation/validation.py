from __future__ import annotations
from .models import *
SCENARIO_TYPES=("tic_quality_case","golden_historical_case","semantic_mutation_case","memory_consistency_case","context_scene_case","cache_reuse_case","resume_reconciliation_case","dual_pass_case","provider_routing_case","multilingual_profile_case","cross_module_case")
RESULT_STATUSES=("passed","failed","insufficient_evidence","invalid_input","conflict","not_applicable","manual_review_required")
DECISIONS=("accept","reject","rollback_to_draft","use_cache","retry_required","blocked","manual_review","not_applicable")
FORBIDDEN_FIXTURE_RESULT_FIELDS=frozenset(("observed_status","observed_decision","module_results","observed_outcomes","candidate_truth","blocking_mutation","cache_reused","retry_required","provider_requests_planned","provider_requests_executed"))
def _reject_fixture_results(value):
    if isinstance(value,dict):
        found=FORBIDDEN_FIXTURE_RESULT_FIELDS.intersection(value)
        if found:raise ValueError("fixture may not declare observed or metric result fields: "+",".join(sorted(found)))
        for item in value.values():_reject_fixture_results(item)
    elif isinstance(value,(list,tuple)):
        for item in value:_reject_fixture_results(item)
def validate_scenario(s:ValidationScenario)->None:
    if not s.scenario_id or s.scenario_type not in SCENARIO_TYPES:raise ValueError("unknown scenario type")
    if s.expected_status not in RESULT_STATUSES:raise ValueError("invalid expected status")
    if s.expected_decision not in DECISIONS:raise ValueError("invalid expected decision")
    if not s.evidence_origin or not s.required_modules:raise ValueError("missing evidence")
    if not isinstance(s.required,bool):raise ValueError("required must be boolean")
    _reject_fixture_results(s.inputs)
    if s.version!="1.0":raise ValueError("unknown case version")
def validate_validation_suite(suite:ValidationSuite)->None:
    if suite.schema_version!=SCHEMA_VERSION or suite.suite_version!=SUITE_VERSION:raise ValueError("unknown schema or suite version")
    ids=set()
    for s in suite.scenarios:
        validate_scenario(s)
        if s.scenario_id in ids:raise ValueError("duplicate scenario ID")
        ids.add(s.scenario_id)
def reject_unsafe(value)->None:
    text=repr(value).lower()
    if "../" in text or "..\\" in text:raise ValueError("path traversal rejected")
    if any(x in text for x in ("authorization: bearer","api_key=","private key","raw_provider_request","raw_provider_response")):raise ValueError("unsafe payload")
def reject_fixture_result_fields(value)->None:_reject_fixture_results(value)
