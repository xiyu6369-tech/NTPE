from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GovernanceContracts:
    production_hook_count: int = 1
    active_production_authorized: bool = False
    production_integration_authorized: bool = False
    automatic_rollout_authorized: bool = False
    formal_output_replacement_authorized: bool = False
    batch107_execution_claim_consumed: bool = True
    batch107_execution_reusable: bool = False
    batch108_retry_globally_forbidden: bool = True
    batch108_fallback_globally_forbidden: bool = True
    batch109_policy_frozen: bool = True
    character_memory_production_write: bool = False
    context_scene_production_write: bool = False
    production_cache_changed: bool = False
    resume_changed: bool = False
    formal_output_changed: bool = False
    dual_pass_candidate_replaces_production: bool = False
    semantic_verification_required: bool = True
    semantic_failure_retains_production: bool = True
    insufficient_evidence_requires_manual_review: bool = True

    def to_dict(self) -> dict[str, object]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}


GOVERNANCE_CONTRACTS = GovernanceContracts()


def get_governance_contracts() -> GovernanceContracts:
    return GOVERNANCE_CONTRACTS
