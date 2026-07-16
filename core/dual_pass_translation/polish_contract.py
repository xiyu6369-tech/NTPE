from __future__ import annotations
from .draft_contract import sha
from .models import *
from .validation import *
def build_polish_request_contract(*,draft,scope,character_memory_selection_fingerprint,context_scene_selection_fingerprint,glossary_fingerprint,quality_policy_version,polish_policy_version):
    if scope.original_draft_hash!=draft.draft_hash:raise DualPassValidationError("stale polish request scope")
    for value,name in ((draft.source_hash,"source_hash"),(draft.draft_hash,"draft_hash"),(character_memory_selection_fingerprint,"character_memory_selection_fingerprint"),(context_scene_selection_fingerprint,"context_scene_selection_fingerprint"),(glossary_fingerprint,"glossary_fingerprint")):valid_hash(value,name)
    scope_hash=sha(str((scope.scope_type.value,scope.start_identifier,scope.end_identifier,scope.selected_text_hash,scope.surrounding_context_hash)))
    return PolishRequestContract(draft.source_hash,draft.draft_hash,scope_hash,character_memory_selection_fingerprint,context_scene_selection_fingerprint,glossary_fingerprint,quality_policy_version,polish_policy_version,True,False)
def create_polish_scope(*,scope_type,original_draft_hash,selected_text,surrounding_context,start_identifier=None,end_identifier=None,outside_before=None,outside_after=None):
    scope=PolishScope(scope_type if isinstance(scope_type,PolishScopeType) else PolishScopeType(scope_type),start_identifier,end_identifier,original_draft_hash,sha(selected_text),sha(surrounding_context),sha(outside_before) if outside_before is not None else None,sha(outside_after) if outside_after is not None else None);validate_scope(scope);return scope
def create_polish_candidate(*,polish_id,draft,polish_text,polish_scope,polish_reason,semantic_invariants=None,created_at,version=1,outside_before=None,outside_after=None):
    if polish_scope.original_draft_hash!=draft.draft_hash:raise DualPassValidationError("stale polish scope")
    candidate=PolishCandidate(polish_id,draft.draft_id,draft.source_hash,draft.draft_hash,polish_text,sha(polish_text),polish_scope,polish_reason,VerificationStatus.INSUFFICIENT_EVIDENCE,(),created_at,version,ArtifactStatus.PREPARED,dict(semantic_invariants or {}),sha(outside_before) if outside_before is not None else None,sha(outside_after) if outside_after is not None else None);validate_candidate(candidate);return candidate
