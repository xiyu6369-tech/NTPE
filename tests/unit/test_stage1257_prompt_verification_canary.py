from __future__ import annotations
import hashlib, json
from pathlib import Path
import pytest
from core.prompt_contract_verification_canary.framework import validate_output
from core.prompt_verification_canary_stage1257.framework import (
    AUTHORIZATION_TOKEN, CANONICAL_ID, FIXTURE_HASH, HISTORICAL_CLAIM_HASH, LOGICAL_ID, SOURCE_HASH,
    Stage1257Config, _claim, build_preflight,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "영희가 민수와 선생님을 번갈아 보며 말했다. ‘선생님, 민수 씨도 함께 가실까요?’"

def test_preclaim_resolution_hashes_and_request_plan() -> None:
    config = Stage1257Config("offline-test", AUTHORIZATION_TOKEN)
    preflight, plan = build_preflight(ROOT, config, clean_override=True)
    assert preflight["status"] == "PASS" and plan is not None
    assert plan["logical_id"] == LOGICAL_ID and plan["canonical_id"] == CANONICAL_ID
    assert [row["name"] for row in preflight["ordered_steps"]][5:9] == ["corpus_identity_resolution", "source_fixture_hash_validation", "request_plan_validation", "stage1257_claim_eligibility_validation"]
    assert hashlib.sha256(str(plan["source"]).encode()).hexdigest() == SOURCE_HASH
    assert hashlib.sha256((ROOT / "tests/fixtures/te_v72_canary/golden_corpus.json").read_bytes()).hexdigest() == FIXTURE_HASH

def test_historical_claim_unchanged_and_new_claim_single_use(tmp_path: Path) -> None:
    historical = ROOT / "artifacts/te_v72_stage1256_prompt_verification_canary/authorization_claim.json"
    assert hashlib.sha256(historical.read_bytes()).hexdigest() == HISTORICAL_CLAIM_HASH
    claim = tmp_path / "claim.json"; config = Stage1257Config("offline-test", AUTHORIZATION_TOKEN)
    _claim(claim, config)
    with pytest.raises(ValueError, match="replay-rejected"): _claim(claim, config)

def test_request_policy_is_hard_limited() -> None:
    assert Stage1257Config("id", AUTHORIZATION_TOKEN).valid()
    assert not Stage1257Config("id", AUTHORIZATION_TOKEN, authorized_request_budget=3).valid()
    assert not Stage1257Config("id", AUTHORIZATION_TOKEN, attempts_per_arm=2, retry=1, fallback=True, parallelism=2, automatic_rerun=True).valid()

def test_structural_failures_are_fail_closed() -> None:
    for output, kwargs in ((SOURCE, {}), ("譯文：她說話。", {}), ("", {"malformed": True}), ("她說……", {"timeout": True})):
        result = validate_output(SOURCE, output, success=bool(output) and not kwargs.get("timeout",False), timeout=kwargs.get("timeout",False), malformed=kwargs.get("malformed",False))
        assert result["status"] == "FAIL"

def test_no_secret_fields_in_preflight_or_plan() -> None:
    preflight, plan = build_preflight(ROOT, Stage1257Config("offline-test", AUTHORIZATION_TOKEN), clean_override=True)
    raw = json.dumps({"preflight":preflight,"plan_metadata":plan["metadata"]}, sort_keys=True).lower()
    assert "authorization:" not in raw and "bearer " not in raw and "api_key" not in raw
