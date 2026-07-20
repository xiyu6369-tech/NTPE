from __future__ import annotations

import hashlib
import json

from tools.generate_te_v720_stage1257a_execution_evidence_sealing import CLAIM, EXPECTED_CLAIM_SHA256, build_artifacts


def test_historical_post_execution_fixture_is_sealed_without_claim_mutation() -> None:
    before = CLAIM.read_bytes()
    artifacts = {path.name: json.loads(data) for path, data in build_artifacts().items()}
    assert hashlib.sha256(before).hexdigest() == EXPECTED_CLAIM_SHA256
    assert CLAIM.read_bytes() == before
    seal = artifacts["historical_execution_seal.json"]
    assert seal["execution_status"] == "completed_fail_closed"
    assert seal["canary_status"] == "inconclusive_baseline_timeout"
    assert seal["provider_requests_consumed"] == 1 and seal["candidate_started"] is False
    lifecycle = artifacts["claim_lifecycle.json"]
    assert lifecycle["claim_status"] == "consumed" and lifecycle["claim_replay_allowed"] is False
    assert artifacts["request_budget_accounting.json"]["unused_request_budget_reusable"] is False


def test_final_activation_is_not_provisional_or_production_authorized() -> None:
    payloads = {path.name: json.loads(data) for path, data in build_artifacts().items()}
    decision = payloads["final_activation_decision.json"]
    assert decision["activation_decision"] == "final_fail_closed"
    assert decision["prompt_contract_verification_canary_passed"] is False
    assert decision["production_authorized"] is False
