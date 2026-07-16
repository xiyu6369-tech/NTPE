from __future__ import annotations

import hashlib
import json

from .executors import SCENARIO_EXECUTORS
from .models import ExecutorOutcome, ValidationScenario, ValidationScenarioResult, ValidationSuite
from .validation import DECISIONS, RESULT_STATUSES, validate_scenario, validate_validation_suite


def _fp(value)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,default=str).encode()).hexdigest()


def _failed_closed(s:ValidationScenario,reason:str)->ValidationScenarioResult:
    payload={"scenario_id":s.scenario_id,"executor_error":reason}
    return ValidationScenarioResult(s.scenario_id,"failed","invalid_input","blocked",(reason,),{"executor_error":reason},(s.evidence_origin,),(),{},None,s.required,False,_fp(payload),"Executor unavailable or raised; scenario failed closed.")


def _validate_outcome(outcome:ExecutorOutcome)->None:
    if not isinstance(outcome,ExecutorOutcome):raise TypeError("executor must return ExecutorOutcome")
    if outcome.candidate_status not in RESULT_STATUSES:raise ValueError("executor returned invalid status")
    if outcome.decision not in DECISIONS:raise ValueError("executor returned invalid decision")
    if not isinstance(outcome.executable_evidence,bool):raise ValueError("invalid executable evidence flag")
    for key,value in outcome.metric_events.items():
        if not isinstance(key,str) or not isinstance(value,int) or isinstance(value,bool) or value<0:raise ValueError("invalid executor metric event")


def run_validation_scenario(s:ValidationScenario)->ValidationScenarioResult:
    validate_scenario(s)
    executor=SCENARIO_EXECUTORS.get(s.scenario_type)
    if executor is None:return _failed_closed(s,"missing_scenario_executor")
    try:
        outcome=executor(s);_validate_outcome(outcome)
    except Exception as exc:
        return _failed_closed(s,f"executor_exception:{type(exc).__name__}:{exc}")
    forbidden=tuple(sorted(set(s.forbidden_outcomes)&set(outcome.observed_outcomes)))
    expected=outcome.candidate_status==s.expected_status and outcome.decision==s.expected_decision and not forbidden
    scenario_status="passed" if expected else "failed"
    evidence=tuple(sorted(outcome.evidence_used or (s.evidence_origin,)))
    modules=dict(sorted(outcome.module_results.items()))
    metrics=dict(sorted(outcome.metric_events.items()))
    payload={"scenario_id":s.scenario_id,"candidate_status":outcome.candidate_status,"decision":outcome.decision,"issues":outcome.issues,"modules":modules,"evidence":evidence,"forbidden":forbidden,"metric_events":metrics,"ground_truth":outcome.ground_truth,"required":s.required,"executable_evidence":outcome.executable_evidence}
    explanation="Expected rejection is a scenario pass." if expected and outcome.candidate_status=="failed" else "Executor outcome matched fixed expectation." if expected else "Executor outcome did not match fixed expectation."
    return ValidationScenarioResult(s.scenario_id,scenario_status,outcome.candidate_status,outcome.decision,outcome.issues,modules,evidence,forbidden,metrics,outcome.ground_truth,s.required,outcome.executable_evidence,_fp(payload),explanation)


def run_validation_suite(suite:ValidationSuite)->tuple[ValidationScenarioResult,...]:
    validate_validation_suite(suite)
    return tuple(run_validation_scenario(s) for s in suite.scenarios)
