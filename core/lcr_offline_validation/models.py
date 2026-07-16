from __future__ import annotations
from dataclasses import dataclass
from typing import Any,Mapping
SCHEMA_VERSION="1.0";SUITE_VERSION="1.0"
@dataclass(frozen=True)
class ValidationCorpusEntry:
    case_id:str;evidence_origin:str;human_approved:bool;synthetic:bool;historical:bool;current_health:bool;evidence_reference:str;payload:Mapping[str,Any]
@dataclass(frozen=True)
class ValidationScenario:
    scenario_id:str;scenario_type:str;source_case_id:str;evidence_origin:str;inputs:Mapping[str,Any];expected_status:str;expected_decision:str;required_modules:tuple[str,...];protected_invariants:tuple[str,...];forbidden_outcomes:tuple[str,...];required:bool;created_at:str;version:str
@dataclass(frozen=True)
class ExecutorOutcome:
    candidate_status:str;decision:str;issues:tuple[str,...];module_results:Mapping[str,Any];evidence_used:tuple[str,...];observed_outcomes:tuple[str,...];metric_events:Mapping[str,int];ground_truth:str|None;executable_evidence:bool
@dataclass(frozen=True)
class ValidationScenarioResult:
    scenario_id:str;scenario_status:str;candidate_status:str;decision:str;issues:tuple[str,...];module_results:Mapping[str,Any];evidence_used:tuple[str,...];forbidden_outcomes_triggered:tuple[str,...];metric_events:Mapping[str,int];ground_truth:str|None;required:bool;executable_evidence:bool;deterministic_fingerprint:str;explanation:str
@dataclass(frozen=True)
class ValidationSuite:
    schema_version:str;suite_version:str;suite_id:str;scenarios:tuple[ValidationScenario,...];corpus_fingerprint:str
@dataclass(frozen=True)
class ValidationMetrics:
    total_scenarios:int;passed_scenarios:int;failed_scenarios:int;insufficient_evidence:int;invalid_inputs:int;manual_reviews:int;blocking_mutations_detected:int;approved_cases_passed:int;historical_failures_rejected:int;false_positive_count:int;false_negative_count:int;cache_reuse_count:int;retry_required_count:int;provider_requests_planned:int;provider_requests_executed:int
@dataclass(frozen=True)
class ValidationReport:
    schema_version:str;suite_version:str;suite_id:str;results:tuple[ValidationScenarioResult,...];metrics:ValidationMetrics;deterministic_fingerprint:str;claim_scope:str
@dataclass(frozen=True)
class ReadinessGateResult:
    status:str;requirements:Mapping[str,bool];reasons:tuple[str,...];meaning:str
