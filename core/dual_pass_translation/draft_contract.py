from __future__ import annotations
import hashlib
from .models import *
from .validation import *
def sha(value):return hashlib.sha256(value.encode("utf-8")).hexdigest()
def create_draft_result(*,draft_id,document_id,chunk_index,source_hash,prompt_identity,source_language,target_language,draft_text,quality_status,quality_evidence=(),semantic_status=SemanticStatus.PASSED,semantic_invariants=None,created_at,version=1,status=ArtifactStatus.VERIFIED,partial=False,timeout=False,cancelled=False,corrupt=False):
    draft=DraftTranslationResult(draft_id,document_id,chunk_index,source_hash,prompt_identity,source_language,target_language,draft_text,sha(draft_text),quality_status if isinstance(quality_status,QualityStatus) else QualityStatus(quality_status),tuple(quality_evidence),semantic_status if isinstance(semantic_status,SemanticStatus) else SemanticStatus(semantic_status),created_at,version,status if isinstance(status,ArtifactStatus) else ArtifactStatus(status),dict(semantic_invariants or {}),partial,timeout,cancelled,corrupt);validate_draft(draft);return draft
def evaluate_draft_eligibility(draft,*,expected_source_hash=None,allow_nonblocking=False):
    reasons=[]
    try:validate_draft(draft)
    except (ValueError,TypeError) as exc:reasons.append(f"invalid:{exc}")
    if not draft.draft_text:reasons.append("empty_draft")
    if expected_source_hash and draft.source_hash!=expected_source_hash:reasons.append("source_hash_mismatch")
    if draft.partial:reasons.append("partial_draft")
    if draft.timeout:reasons.append("timeout_draft")
    if draft.cancelled:reasons.append("cancelled_draft")
    if draft.corrupt:reasons.append("corrupt_draft")
    if draft.semantic_status!=SemanticStatus.PASSED:reasons.append("semantic_not_passed")
    quality_ok=draft.quality_status==QualityStatus.PASSED or (allow_nonblocking and draft.quality_status==QualityStatus.PASSED_WITH_NONBLOCKING_ISSUES)
    if not quality_ok:reasons.append("quality_not_eligible")
    if draft.status!=ArtifactStatus.VERIFIED:reasons.append("draft_not_verified")
    return {"eligible":not reasons,"reasons":tuple(reasons)}
