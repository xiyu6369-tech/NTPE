from __future__ import annotations
import json,re
from datetime import datetime
from .models import *
class DualPassValidationError(ValueError):pass
_SHA=re.compile(r"^[0-9a-f]{64}$",re.I);_ID=re.compile(r"^[A-Za-z0-9._:-]{1,180}$")
_SECRET=(re.compile(r"nvapi-[A-Za-z0-9._-]{16,}",re.I),re.compile(r"Bearer\s+[A-Za-z0-9._-]{12,}",re.I),re.compile(r"Authorization\s*:\s*\S+",re.I),re.compile(r"api[_-]?key\s*=\s*\S+",re.I),re.compile(r"-----BEGIN .*PRIVATE KEY-----",re.I))
def timestamp(value,name):
    try:parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
    except (AttributeError,ValueError) as exc:raise DualPassValidationError(f"invalid {name}") from exc
    if parsed.tzinfo is None:raise DualPassValidationError(f"timezone required for {name}")
def safe_id(value,name):
    if not isinstance(value,str) or not _ID.fullmatch(value) or "/" in value or "\\" in value or value in {".",".."}:raise DualPassValidationError(f"invalid {name}")
def safe_text(value,name):
    if not isinstance(value,str) or not value.strip() or len(value)>20000:raise DualPassValidationError(f"invalid {name}")
    if any(p.search(value) for p in _SECRET):raise DualPassValidationError(f"secret-like {name}")
def safe_mapping(value,name):
    forbidden={"raw_provider_response","provider_response","provider_request","request_headers","authorization","api_key","credentials"}
    def walk(item):
        if isinstance(item,dict):
            for key,child in item.items():
                if str(key).lower() in forbidden:raise DualPassValidationError(f"forbidden {name} field")
                walk(child)
        elif isinstance(item,(list,tuple)): 
            for child in item:walk(child)
        elif isinstance(item,str) and any(p.search(item) for p in _SECRET):raise DualPassValidationError(f"secret-like {name}")
    walk(value)
def valid_hash(value,name):
    if not _SHA.fullmatch(value or ""):raise DualPassValidationError(f"invalid {name}")
def validate_scope(scope):
    valid_hash(scope.original_draft_hash,"original_draft_hash");valid_hash(scope.selected_text_hash,"selected_text_hash");valid_hash(scope.surrounding_context_hash,"surrounding_context_hash")
    if scope.scope_type==PolishScopeType.NONE:return
    if scope.scope_type!=PolishScopeType.FULL_CHUNK and (not scope.start_identifier or not scope.end_identifier):raise DualPassValidationError("bounded scope requires identifiers")
def validate_draft(draft):
    safe_id(draft.draft_id,"draft_id");safe_id(draft.document_id,"document_id");valid_hash(draft.source_hash,"source_hash");valid_hash(draft.prompt_identity,"prompt_identity");valid_hash(draft.draft_hash,"draft_hash");timestamp(draft.created_at,"created_at")
    if draft.draft_text:safe_text(draft.draft_text,"draft_text")
    safe_mapping(draft.quality_evidence,"quality_evidence");safe_mapping(draft.semantic_invariants,"semantic_invariants")
    if draft.chunk_index<0 or draft.version<1:raise DualPassValidationError("invalid draft numeric field")
    if draft.draft_text and __import__("hashlib").sha256(draft.draft_text.encode()).hexdigest()!=draft.draft_hash:raise DualPassValidationError("draft hash mismatch")
def validate_candidate(candidate):
    safe_id(candidate.polish_id,"polish_id");safe_id(candidate.draft_id,"draft_id");valid_hash(candidate.source_hash,"source_hash");valid_hash(candidate.draft_hash,"draft_hash");valid_hash(candidate.polish_hash,"polish_hash");safe_text(candidate.polish_text,"polish_text");timestamp(candidate.created_at,"created_at");validate_scope(candidate.polish_scope)
    if __import__("hashlib").sha256(candidate.polish_text.encode()).hexdigest()!=candidate.polish_hash:raise DualPassValidationError("polish hash mismatch")
    safe_text(candidate.polish_reason,"polish_reason");safe_mapping(candidate.semantic_invariants,"semantic_invariants")
    if candidate.version<1:raise DualPassValidationError("invalid candidate version")
def validate_trigger(trigger):
    safe_id(trigger.trigger_id,"trigger_id");validate_scope(trigger.scope)
    safe_mapping(trigger.evidence,"trigger evidence")
    if trigger.scope.scope_type==PolishScopeType.NONE and trigger.trigger_type!=TriggerType.NO_TRIGGER:raise DualPassValidationError("eligible trigger requires explicit scope")
    if not 0<=trigger.confidence<=1 or trigger.estimated_cost<0 or trigger.estimated_quality_value<0:raise DualPassValidationError("invalid trigger metric")
