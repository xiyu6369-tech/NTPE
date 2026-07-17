from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from .pilot_authorization import PilotAuthorization,validate_authorization

@dataclass(frozen=True)
class PilotPreparationResult:
    status:str; reason_codes:tuple[str,...]; package:object|None; provider_requests:int=0; network_requests:int=0; translation_replaced:bool=False; output_modified:bool=False; resume_modified:bool=False; cache_modified:bool=False; active_integration:bool=False

def prepare_bounded_dual_pass_pilot(*,planning,authorization:PilotAuthorization|None,document_id:str,chunk_id:str,source_hash:str,provider_id:str,model_id:str,now:str,target_count:int=1,rollback_baseline_hash:str="") -> PilotPreparationResult:
    if target_count!=1:return PilotPreparationResult("blocked",("ambiguous_target_chunk",),None)
    if getattr(planning,"eligibility","") not in {"dual_pass_candidate","selective_polish_candidate"}:return PilotPreparationResult("blocked",("planning_not_pilot_eligible",),None)
    if not rollback_baseline_hash:return PilotPreparationResult("blocked",("missing_rollback_baseline",),None)
    if authorization is None:return PilotPreparationResult("blocked",("explicit_execution_authorization_missing",),None)
    valid,reasons=validate_authorization(authorization,document_id=document_id,chunk_id=chunk_id,source_hash=source_hash,provider_id=provider_id,model_id=model_id,now=now)
    if not valid:return PilotPreparationResult("blocked",reasons,None)
    package=MappingProxyType({"chunk_id":chunk_id,"source_hash":source_hash,"provider_id":provider_id,"model_id":model_id,"draft_request_limit":1,"polish_request_limit":1,"total_request_limit":2,"timeout_seconds":authorization.timeout_seconds,"retry_limit":authorization.retry_limit,"rollback_baseline_hash":rollback_baseline_hash,"output_replacement_allowed":False,"resume_write_allowed":False,"cache_write_allowed":False})
    return PilotPreparationResult("prepared",(),package)
