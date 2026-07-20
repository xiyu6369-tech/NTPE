from __future__ import annotations

import json

from core.prompt_contract_verification_canary.candidate_structural_canary import PREPARATION_STEPS, READY_GATE
from tools.generate_te_v720_stage1258_candidate_structural_verification_canary import build_preparation_artifacts


def test_stage1258_integration_preparation_is_candidate_only_and_fail_closed() -> None:
    artifacts = {path.name: json.loads(data) for path, data in build_preparation_artifacts().items()}
    template = artifacts["preflight_template.json"]
    assert [row["name"] for row in template["ordered_steps"][:13]] == list(PREPARATION_STEPS)
    assert template["failure_through_step_13"] == {
        "claim_created": False, "provider_requests": 0, "fail_closed": True,
    }
    plan = artifacts["request_plan.json"]
    assert plan["arm"] == "candidate" and plan["baseline_included"] is False
    assert plan["maximum_provider_requests"] == 1
    activation = artifacts["activation_contract.json"]
    assert activation["gate_before_execution"] == READY_GATE
    assert activation["formal_output_replacement_authorized"] is False
