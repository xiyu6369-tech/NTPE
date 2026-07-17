from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone

@dataclass(frozen=True)
class PilotAuthorization:
    authorization_id:str; authorized_by:str; authorized_at:str; expires_at:str; target_document_id:str; target_chunk_id:str; source_hash:str; provider_id:str; model_id:str; draft_request_limit:int=1; polish_request_limit:int=1; total_request_limit:int=2; timeout_seconds:int=20; retry_limit:int=0; fallback_allowed:bool=False; output_replacement_allowed:bool=False; resume_write_allowed:bool=False; cache_write_allowed:bool=False; provider_execution:bool=False; rollback_required:bool=True; explicit_execution_authorization:bool=False

def validate_authorization(value:PilotAuthorization,*,document_id:str,chunk_id:str,source_hash:str,provider_id:str,model_id:str,now:str) -> tuple[bool,tuple[str,...]]:
    reasons=[]
    def stamp(text):
        if not isinstance(text,str) or not text.endswith('Z'): raise ValueError()
        return datetime.fromisoformat(text[:-1]+'+00:00')
    try:
        authorized,expires,current=stamp(value.authorized_at),stamp(value.expires_at),stamp(now)
        if authorized>current: reasons.append('authorized_at_in_future')
        if authorized>=expires: reasons.append('invalid_authorization_interval')
    except ValueError: reasons.append('malformed_timestamp'); authorized=expires=current=None
    if not value.explicit_execution_authorization: reasons.append("explicit_execution_authorization_missing")
    if expires is not None and expires<=current: reasons.append("authorization_expired")
    for actual,expected,name in ((value.target_document_id,document_id,"document"),(value.target_chunk_id,chunk_id,"chunk"),(value.source_hash,source_hash,"source_hash"),(value.provider_id,provider_id,"provider"),(value.model_id,model_id,"model")):
        if actual!=expected: reasons.append(name+"_mismatch")
    if (value.draft_request_limit,value.polish_request_limit,value.total_request_limit)!=(1,1,2): reasons.append("invalid_request_budget")
    if value.timeout_seconds<=0 or value.timeout_seconds>25 or value.retry_limit<0 or value.retry_limit>1: reasons.append("invalid_timeout_or_retry_budget")
    if value.fallback_allowed or value.output_replacement_allowed or value.resume_write_allowed or value.cache_write_allowed or value.provider_execution or not value.rollback_required: reasons.append("unsafe_preparation_mode_policy")
    return not reasons,tuple(reasons)
