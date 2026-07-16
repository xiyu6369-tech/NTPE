from __future__ import annotations
import json
from .models import *
from .validation import reject_unsafe,validate_validation_suite
def serialize_validation_suite(suite:ValidationSuite)->str:
    from dataclasses import asdict
    validate_validation_suite(suite);return json.dumps(asdict(suite),ensure_ascii=False,sort_keys=True,separators=(",",":"))
def deserialize_validation_suite(payload:str)->ValidationSuite:
    try:value=json.loads(payload)
    except (TypeError,json.JSONDecodeError) as exc:raise ValueError("malformed JSON") from exc
    reject_unsafe(value)
    try:
        scenarios=tuple(ValidationScenario(scenario_id=x["scenario_id"],scenario_type=x["scenario_type"],source_case_id=x["source_case_id"],evidence_origin=x["evidence_origin"],inputs=x["inputs"],expected_status=x["expected_status"],expected_decision=x["expected_decision"],required_modules=tuple(x["required_modules"]),protected_invariants=tuple(x["protected_invariants"]),forbidden_outcomes=tuple(x["forbidden_outcomes"]),required=x["required"],created_at=x["created_at"],version=x["version"]) for x in value["scenarios"])
        suite=ValidationSuite(value["schema_version"],value["suite_version"],value["suite_id"],scenarios,value["corpus_fingerprint"])
    except (KeyError,TypeError) as exc:raise ValueError("missing suite field") from exc
    validate_validation_suite(suite);return suite
