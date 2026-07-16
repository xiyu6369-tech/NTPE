from __future__ import annotations
import hashlib,json
from dataclasses import asdict
from .metrics import calculate_validation_metrics
from .models import *
def build_validation_report(suite:ValidationSuite,results:tuple[ValidationScenarioResult,...])->ValidationReport:
    metrics=calculate_validation_metrics(suite,results);payload={"suite":suite.suite_id,"results":[asdict(x) for x in results],"metrics":asdict(metrics)};fp=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest();return ValidationReport(SCHEMA_VERSION,SUITE_VERSION,suite.suite_id,results,metrics,fp,"Fixed Golden/TIC scenarios only; not Production readiness.")
def evaluate_lcr_offline_readiness(report:ValidationReport,*,all_required_scenarios_present:bool,production_boundaries_unchanged:bool,all_regressions_pass:bool,determinism_pass:bool)->ReadinessGateResult:
    m=report.metrics;required=[x for x in report.results if x.required];required_executable=bool(required) and all(x.executable_evidence for x in required);required_pass=bool(required) and all(x.scenario_status=="passed" for x in required);req={"all_required_scenarios_present":all_required_scenarios_present,"required_executable_evidence_complete":required_executable,"all_required_executable_scenarios_pass":required_pass,"all_human_approved_cases_pass":m.false_negative_count==0 and m.approved_cases_passed>0,"false_positive_count_zero":m.false_positive_count==0,"false_negative_count_zero":m.false_negative_count==0,"provider_requests_executed_zero":m.provider_requests_executed==0,"production_boundaries_unchanged":production_boundaries_unchanged,"all_regressions_pass":all_regressions_pass,"determinism_pass":determinism_pass}
    status="ready" if all(req.values()) else "not_ready";reasons=tuple(k for k,v in req.items() if not v)
    if not required_executable:reasons=("executable_scenario_evidence_incomplete",)+tuple(x for x in reasons if x!="required_executable_evidence_complete")
    return ReadinessGateResult(status,req,reasons,"ready for Batch 10 controlled integration planning only" if status=="ready" else "not ready for next planning stage")
