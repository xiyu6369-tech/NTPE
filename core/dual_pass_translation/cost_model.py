from __future__ import annotations
import math
from .models import *
from .validation import DualPassValidationError
def estimate_provider_cost(*,mode,draft_input_chars,draft_output_chars,polish_input_chars=0,polish_output_chars=0,provider_health=ProviderHealth.UNKNOWN,cache_reuse_possible=False,retry_allowance=0,maximum_polish_requests_per_chunk=1):
    mode=mode if isinstance(mode,TranslationMode) else TranslationMode(mode);health=provider_health if isinstance(provider_health,ProviderHealth) else ProviderHealth(provider_health)
    if min(draft_input_chars,draft_output_chars,polish_input_chars,polish_output_chars,retry_allowance,maximum_polish_requests_per_chunk)<0:raise DualPassValidationError("negative cost input")
    if maximum_polish_requests_per_chunk>1:raise DualPassValidationError("maximum polish requests per chunk is one")
    requests=1 if mode==TranslationMode.SINGLE_PASS else 2 if mode in {TranslationMode.DUAL_PASS,TranslationMode.SELECTIVE_POLISH} else 0
    if cache_reuse_possible and mode in {TranslationMode.DUAL_PASS,TranslationMode.SELECTIVE_POLISH}:requests=1
    if health==ProviderHealth.UNAVAILABLE and requests>1:raise DualPassValidationError("provider unavailable for polish")
    draft_reused=cache_reuse_possible and mode in {TranslationMode.DUAL_PASS,TranslationMode.SELECTIVE_POLISH}
    inputs=math.ceil(((0 if draft_reused else draft_input_chars)+(polish_input_chars if mode in {TranslationMode.DUAL_PASS,TranslationMode.SELECTIVE_POLISH} else 0))/4);outputs=math.ceil(((0 if draft_reused else draft_output_chars)+(polish_output_chars if mode in {TranslationMode.DUAL_PASS,TranslationMode.SELECTIVE_POLISH} else 0))/4);risk={ProviderHealth.HEALTHY:.1,ProviderHealth.DEGRADED:.65,ProviderHealth.UNAVAILABLE:1.0,ProviderHealth.UNKNOWN:.45}[health]
    return ProviderCostEstimate(requests,inputs,outputs,inputs+outputs,requests*(1+risk)*30,risk,min(1.0,risk+.15),cache_reuse_possible,requests+retry_allowance,maximum_polish_requests_per_chunk)
