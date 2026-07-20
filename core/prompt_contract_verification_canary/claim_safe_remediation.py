from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Callable, Mapping

from core.translation_quality_provider_canary.framework import _build_prompts
from .corpus_identity import build_corpus_identity_contract, resolve_canary_corpus_id

READINESS_GATE = "translation_quality_integration_ready_for_controlled_canary"
FIXTURE = "tests/fixtures/te_v72_canary/golden_corpus.json"

class ClaimLifecycleError(ValueError): pass

def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

@dataclass(frozen=True)
class ClaimSafeRequestPlan:
    logical_id: str
    canonical_id: str
    source_text: str
    source_hash: str
    fixture_hash: str
    system_prompt: str
    baseline_prompt: str
    candidate_prompt: str
    integration_metadata: Mapping[str, object]

@dataclass(frozen=True)
class ClaimSafeValidation:
    status: str
    ordered_steps: tuple[Mapping[str, object], ...]
    plan: ClaimSafeRequestPlan | None
    claim_created: bool = False
    provider_requests: int = 0

    def to_dict(self) -> dict[str, object]:
        return {"status": self.status, "ordered_steps": [dict(row) for row in self.ordered_steps],
                "claim_created": self.claim_created, "provider_requests": self.provider_requests,
                "resolved_canonical_id": self.plan.canonical_id if self.plan else None}

def validate_before_claim(
    *, root: str | Path, logical_id: str, claim_path: str | Path,
    prerequisite_checks: Mapping[str, bool],
) -> ClaimSafeValidation:
    base = Path(root).resolve(); claim = Path(claim_path)
    names = ("git_worktree_checks", "artifact_hash_checks", "readiness_gate_checks", "authorization_budget_checks")
    steps: list[dict[str, object]] = []
    for name in names:
        steps.append({"step": len(steps) + 1, "name": name, "passed": prerequisite_checks.get(name) is True})
    plan: ClaimSafeRequestPlan | None = None
    try:
        fixture = base / FIXTURE
        contract = build_corpus_identity_contract(fixture)
        resolution = resolve_canary_corpus_id(logical_id, (contract,))
        steps.append({"step": 5, "name": "corpus_logical_id_resolution", "passed": True,
                      "logical_id": logical_id, "canonical_id": resolution.canonical_id})
        payload = json.loads(fixture.read_text(encoding="utf-8"))
        exact = [case for case in payload.get("cases", []) if case.get("case_id") == resolution.canonical_id]
        source_ok = len(exact) == 1 and _sha(str(exact[0].get("source_text", "")).encode("utf-8")) == resolution.source_hash
        steps.append({"step": 6, "name": "corpus_source_hash_validation", "passed": source_ok})
        prompts = _build_prompts(resolution.logical_id, str(exact[0]["source_text"])) if source_ok else None
        steps.append({"step": 7, "name": "request_plan_construction_validation", "passed": prompts is not None})
        if prompts:
            plan = ClaimSafeRequestPlan(resolution.logical_id, resolution.canonical_id, str(exact[0]["source_text"]),
                                        resolution.source_hash, resolution.fixture_hash, prompts[0], prompts[1], prompts[2], prompts[3])
    except Exception as exc:
        steps.append({"step": 5, "name": "corpus_logical_id_resolution", "passed": False,
                      "error": f"{type(exc).__name__}:{exc}"})
        steps.append({"step": 6, "name": "corpus_source_hash_validation", "passed": False})
        steps.append({"step": 7, "name": "request_plan_construction_validation", "passed": False})
    steps.append({"step": 8, "name": "claim_eligibility_validation", "passed": not claim.exists()})
    passed = all(bool(row["passed"]) for row in steps)
    return ClaimSafeValidation("PASS" if passed else "FAIL", tuple(steps), plan if passed else None)

def create_claim_after_validation(validation: ClaimSafeValidation, claim_path: str | Path, payload: Mapping[str, object]) -> None:
    if validation.status != "PASS" or validation.plan is None:
        raise ClaimLifecycleError("claim-forbidden-before-complete-validation")
    path = Path(claim_path); path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream: stream.write(_canonical(dict(payload)))
    except FileExistsError as exc:
        raise ClaimLifecycleError("claim-replay-rejected") from exc

def run_with_fail_closed_capture(
    *, validation: ClaimSafeValidation, claim_path: str | Path, claim_payload: Mapping[str, object],
    artifact_root: str | Path, executor: Callable[[ClaimSafeRequestPlan], Mapping[str, object]],
) -> dict[str, object]:
    root = Path(artifact_root); root.mkdir(parents=True, exist_ok=True)
    if validation.status != "PASS" or validation.plan is None:
        summary = {"status": "preclaim_validation_failed", "claim_created": False, "provider_requests": 0}
        (root / "execution_summary.json").write_bytes(_canonical(summary)); return summary
    create_claim_after_validation(validation, claim_path, claim_payload)
    try:
        result = dict(executor(validation.plan))
        result.setdefault("status", "complete")
        return result
    except Exception as exc:
        summary = {"status": "execution_failed_closed", "claim_created": True, "claim_replay_allowed": False,
                   "provider_requests": 0, "failure_phase": "post_claim_execution",
                   "exception_type": type(exc).__name__}
        decision = {"prompt_contract_verification_canary_passed": False, "activation_gate": READINESS_GATE,
                    "active_production_authorized": False, "automatic_rollout_authorized": False,
                    "formal_output_replacement_authorized": False, "production_authorized": False}
        (root / "execution_summary.json").write_bytes(_canonical(summary))
        (root / "activation_decision.json").write_bytes(_canonical(decision))
        return summary
