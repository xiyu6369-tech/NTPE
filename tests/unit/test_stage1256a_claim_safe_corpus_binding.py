from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from core.prompt_contract_verification_canary.claim_safe_remediation import (
    ClaimLifecycleError, create_claim_after_validation, run_with_fail_closed_capture, validate_before_claim,
)
from core.prompt_contract_verification_canary.corpus_identity import (
    AmbiguousCorpusIdentityError, CorpusIdentityContract, DuplicateCorpusAliasError,
    UnknownCorpusIdentityError, build_corpus_identity_contract, resolve_canary_corpus_id,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/fixtures/te_v72_canary/golden_corpus.json"
PREREQUISITES = {name: True for name in ("git_worktree_checks", "artifact_hash_checks", "readiness_gate_checks", "authorization_budget_checks")}

def test_logical_and_canonical_ids_resolve_exactly() -> None:
    contract = build_corpus_identity_contract(FIXTURE)
    assert resolve_canary_corpus_id("canary-001", (contract,)).canonical_id == "canary-001-character-honorific"
    assert resolve_canary_corpus_id(contract.canonical_id, (contract,)).canonical_id == contract.canonical_id

def test_unknown_duplicate_and_ambiguous_mappings_fail_closed() -> None:
    contract = build_corpus_identity_contract(FIXTURE)
    with pytest.raises(UnknownCorpusIdentityError): resolve_canary_corpus_id("canary-999", (contract,))
    with pytest.raises(DuplicateCorpusAliasError): resolve_canary_corpus_id("dup", (replace(contract, aliases=("dup",)), replace(contract, canonical_id="other", aliases=("dup",))))
    with pytest.raises(AmbiguousCorpusIdentityError): resolve_canary_corpus_id(contract.canonical_id, (contract, replace(contract, canonical_id="other", aliases=(contract.canonical_id,))))

def test_resolution_and_request_plan_precede_claim_creation(tmp_path: Path) -> None:
    claim = tmp_path / "claim.json"
    result = validate_before_claim(root=ROOT, logical_id="canary-001", claim_path=claim, prerequisite_checks=PREREQUISITES)
    assert result.status == "PASS" and not claim.exists()
    assert [row["name"] for row in result.ordered_steps][4:8] == ["corpus_logical_id_resolution", "corpus_source_hash_validation", "request_plan_construction_validation", "claim_eligibility_validation"]
    create_claim_after_validation(result, claim, {"single_use": True})
    assert claim.exists()

def test_resolution_failure_never_creates_claim(tmp_path: Path) -> None:
    claim = tmp_path / "claim.json"
    result = validate_before_claim(root=ROOT, logical_id="unknown", claim_path=claim, prerequisite_checks=PREREQUISITES)
    assert result.status == "FAIL" and not claim.exists()
    with pytest.raises(ClaimLifecycleError): create_claim_after_validation(result, claim, {})
    assert not claim.exists()

def test_post_claim_exception_is_captured_and_claim_cannot_replay(tmp_path: Path) -> None:
    claim = tmp_path / "claim.json"; artifacts = tmp_path / "artifacts"
    result = validate_before_claim(root=ROOT, logical_id="canary-001", claim_path=claim, prerequisite_checks=PREREQUISITES)
    summary = run_with_fail_closed_capture(validation=result, claim_path=claim, claim_payload={"single_use": True}, artifact_root=artifacts,
                                           executor=lambda _: (_ for _ in ()).throw(RuntimeError("offline-test")))
    assert summary["status"] == "execution_failed_closed" and summary["provider_requests"] == 0
    with pytest.raises(ClaimLifecycleError): create_claim_after_validation(result, claim, {})

def test_historical_claim_is_immutable_and_not_replayable() -> None:
    claim = ROOT / "tests/fixtures/te_v72_canary/authorization_claim.json"
    before = claim.read_bytes()
    result = validate_before_claim(root=ROOT, logical_id="canary-001", claim_path=claim, prerequisite_checks=PREREQUISITES)
    assert result.status == "FAIL" and result.ordered_steps[-1]["passed"] is False
    assert claim.read_bytes() == before
