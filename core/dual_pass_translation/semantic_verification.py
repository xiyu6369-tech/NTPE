from __future__ import annotations
from .models import *
from .draft_contract import sha
from .validation import validate_candidate,validate_draft
_COMPARE={"subject_references":"subject_reference_shift","pronoun_references":"pronoun_reference_shift","numbers":"number_change","times":"time_change","negations":"negation_change","causal_links":"causal_change","relationships":"relationship_change","speakers":"speaker_change","point_of_view":"point_of_view_change","locations":"location_change","events":"event_change","ambiguity_markers":"ambiguity_loss","dialogue_boundaries":"dialogue_boundary_change","glossary_terms":"glossary_violation"}
_BLOCKING=set(_COMPARE.values())|{"named_entity_change","name_completion","omission","addition","out_of_scope_change"}
def _issue(kind,draft_value,polish_value,scope,confidence=1.0):
    severity=Severity.BLOCKING if kind in _BLOCKING else Severity.NONBLOCKING
    return SemanticIssue(f"semantic:{kind}",kind,severity,"structured invariant",repr(draft_value),repr(polish_value),scope,kind in _BLOCKING,confidence,"rollback_to_verified_draft" if kind in _BLOCKING else "review")
def verify_polish_candidate(source,verified_draft,polish_candidate,*,semantic_policy,approved_evidence=None):
    try:validate_draft(verified_draft);validate_candidate(polish_candidate)
    except (ValueError,TypeError):return SemanticVerificationResult(VerificationStatus.INVALID,(),(),str(semantic_policy.get("version","unknown")),polish_candidate.polish_id,0)
    if sha(source)!=verified_draft.source_hash or polish_candidate.source_hash!=verified_draft.source_hash or polish_candidate.draft_hash!=verified_draft.draft_hash or polish_candidate.polish_scope.original_draft_hash!=verified_draft.draft_hash:return SemanticVerificationResult(VerificationStatus.INVALID,(_issue("out_of_scope_change","identity","mismatch","identity"),),(),str(semantic_policy.get("version","unknown")),polish_candidate.polish_id,1)
    expected_scope=semantic_policy.get("expected_scope",{})
    for field in ("selected_text_hash","surrounding_context_hash","start_identifier","end_identifier"):
        if field in expected_scope and getattr(polish_candidate.polish_scope,field)!=expected_scope[field]:return SemanticVerificationResult(VerificationStatus.INVALID,(_issue("out_of_scope_change",expected_scope[field],getattr(polish_candidate.polish_scope,field),field),),(),str(semantic_policy.get("version","unknown")),polish_candidate.polish_id,1)
    required=tuple(semantic_policy.get("required_invariants",("subject_references","pronoun_references","named_entities","numbers","times","negations","causal_links","content_units","ambiguity_markers")))
    draft=dict(verified_draft.semantic_invariants);polish=dict(polish_candidate.semantic_invariants)
    missing=[x for x in required if x not in draft or x not in polish]
    if missing:return SemanticVerificationResult(VerificationStatus.INSUFFICIENT_EVIDENCE,(),tuple(x for x in required if x not in missing),str(semantic_policy.get("version","unknown")),polish_candidate.polish_id,0)
    issues=[]
    for key,kind in _COMPARE.items():
        if key in draft and key in polish and draft[key]!=polish[key]:issues.append(_issue(kind,draft[key],polish[key],polish_candidate.polish_scope.scope_type.value))
    if "named_entities" in draft and "named_entities" in polish:
        old=set(draft["named_entities"]);new=set(polish["named_entities"])
        if new-old:issues.append(_issue("name_completion" if any(len(x)>len(y) and y in x for x in new-old for y in old) else "named_entity_change",sorted(old),sorted(new),"named_entities"))
        elif old!=new:issues.append(_issue("named_entity_change",sorted(old),sorted(new),"named_entities"))
    if "content_units" in draft and "content_units" in polish:
        old=set(draft["content_units"]);new=set(polish["content_units"])
        if old-new:issues.append(_issue("omission",sorted(old-new),(),"content_units"))
        if new-old:issues.append(_issue("addition",(),sorted(new-old),"content_units"))
    scope=polish_candidate.polish_scope
    if scope.scope_type!=PolishScopeType.FULL_CHUNK and ((scope.outside_before_hash and polish_candidate.outside_before_hash!=scope.outside_before_hash) or (scope.outside_after_hash and polish_candidate.outside_after_hash!=scope.outside_after_hash)):issues.append(_issue("out_of_scope_change","unchanged outside scope","modified","outside_scope"))
    blocking=sum(x.blocking for x in issues);status=VerificationStatus.FAILED if blocking else VerificationStatus.PASSED
    return SemanticVerificationResult(status,tuple(issues),required,str(semantic_policy.get("version","unknown")),polish_candidate.polish_id,blocking)
