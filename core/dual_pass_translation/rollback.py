from __future__ import annotations
from dataclasses import replace
from .draft_contract import evaluate_draft_eligibility,sha
from .models import *
from .validation import DualPassValidationError
def decide_polish_rollback(draft,candidate,verification):
    eligible=evaluate_draft_eligibility(draft)
    if not eligible["eligible"]:return RollbackDecision(RollbackAction.BLOCK_OUTPUT,"invalid_draft_baseline",None,None,draft.draft_id,candidate.polish_id if candidate else None,True)
    if candidate is None:return RollbackDecision(RollbackAction.ACCEPT_POLISH if False else RollbackAction.ROLLBACK_TO_DRAFT,"no_polish_candidate",draft.draft_text,draft.draft_hash,draft.draft_id,None,True)
    if verification.status==VerificationStatus.PASSED:return RollbackDecision(RollbackAction.ACCEPT_POLISH,"semantic_verification_passed",candidate.polish_text,candidate.polish_hash,draft.draft_id,candidate.polish_id,True)
    if verification.status in {VerificationStatus.FAILED,VerificationStatus.INVALID}:return RollbackDecision(RollbackAction.ROLLBACK_TO_DRAFT,"polish_verification_failed",draft.draft_text,draft.draft_hash,draft.draft_id,candidate.polish_id,True)
    return RollbackDecision(RollbackAction.MANUAL_REVIEW_REQUIRED,"insufficient_evidence",None,None,draft.draft_id,candidate.polish_id,True)
def apply_polish_rollback(draft,candidate,decision):
    if decision.draft_id!=draft.draft_id or (candidate and decision.polish_id not in {None,candidate.polish_id}):raise DualPassValidationError("rollback artifact mismatch")
    if decision.action==RollbackAction.ACCEPT_POLISH:
        if not candidate or decision.selected_hash!=candidate.polish_hash:raise DualPassValidationError("invalid polish acceptance")
        updated=replace(candidate,status=ArtifactStatus.FINAL,verification_status=VerificationStatus.PASSED);kind="polish"
    elif decision.action==RollbackAction.ROLLBACK_TO_DRAFT:
        if decision.selected_hash!=draft.draft_hash:raise DualPassValidationError("invalid draft rollback hash")
        updated=replace(candidate,status=ArtifactStatus.REJECTED,verification_status=VerificationStatus.FAILED) if candidate else None;kind="draft"
    else:updated=replace(candidate,status=ArtifactStatus.REJECTED,verification_status=VerificationStatus.INVALID) if candidate else None;kind="blocked"
    return {"selected_kind":kind,"final_text":decision.selected_text,"final_hash":decision.selected_hash,"draft_id":draft.draft_id,"polish_candidate":updated,"polish_evidence_preserved":candidate is not None}
