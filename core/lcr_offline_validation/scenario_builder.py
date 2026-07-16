from __future__ import annotations
from .case_loading import corpus_fingerprint
from .models import *
from .validation import validate_scenario,validate_validation_suite
def create_validation_scenario(**values)->ValidationScenario:
    item=ValidationScenario(**values);validate_scenario(item);return item
def build_validation_suite(entries:tuple[ValidationCorpusEntry,...],*,suite_id="lcr-batch9-fixed-offline-suite")->ValidationSuite:
    scenarios=[]
    for entry in entries:
        p=dict(entry.payload)
        scenarios.append(create_validation_scenario(scenario_id=entry.case_id,scenario_type=p["scenario_type"],source_case_id=p.get("source_case_id",entry.case_id),evidence_origin=entry.evidence_origin,inputs=p["inputs"],expected_status=p["expected_status"],expected_decision=p["expected_decision"],required_modules=tuple(p["required_modules"]),protected_invariants=tuple(p.get("protected_invariants",())),forbidden_outcomes=tuple(p.get("forbidden_outcomes",())),required=p.get("required",True),created_at=p.get("created_at","2026-07-16T00:00:00Z"),version=p.get("version","1.0")))
    suite=ValidationSuite(SCHEMA_VERSION,SUITE_VERSION,suite_id,tuple(sorted(scenarios,key=lambda x:x.scenario_id)),corpus_fingerprint(entries));validate_validation_suite(suite);return suite
