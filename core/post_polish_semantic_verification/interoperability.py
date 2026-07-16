from __future__ import annotations

from .models import VerificationDecision, VerificationStatus
from .verification import verify_post_polish_semantics


def verify_dual_pass_polish(*args, **kwargs):
    return verify_post_polish_semantics(*args, **kwargs)


def build_batch5_verification_view(result) -> dict:
    return {"verification_authority": "LCR Batch 6 offline core", "production_integrated": False, "status": result.status.value, "decision": result.decision.value, "candidate_acceptable": result.status is VerificationStatus.PASSED}


def build_rollback_recommendation(result, *, draft_identity: str, polish_identity: str | None = None) -> dict:
    selected = polish_identity if result.decision is VerificationDecision.ACCEPT_POLISH else draft_identity if result.decision is VerificationDecision.ROLLBACK_TO_DRAFT else None
    return {"action": result.decision.value, "selected_identity": selected, "draft_identity": draft_identity, "polish_identity": polish_identity, "failed_polish_evidence_preserved": result.status is not VerificationStatus.PASSED, "final_polish_cache_eligible": result.status is VerificationStatus.PASSED}
