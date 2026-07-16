from __future__ import annotations

FAILURE_TYPES=("connect_timeout","read_timeout","provider_timeout","rate_limit","resource_exhausted","http_5xx","http_4xx","authentication_failure","invalid_request","malformed_response","empty_response","partial_response","quality_failure","semantic_failure","policy_failure","cancelled","unknown_failure")
_RETRYABLE={"connect_timeout","read_timeout","provider_timeout","rate_limit","resource_exhausted","http_5xx","empty_response"}
_FALLBACK={"connect_timeout","read_timeout","provider_timeout","rate_limit","resource_exhausted","http_5xx","empty_response","malformed_response","partial_response"}


def classify_provider_failure(failure_type:str)->dict:
    if failure_type not in FAILURE_TYPES: raise ValueError("unknown failure type")
    return {"failure_type":failure_type,"retryable":failure_type in _RETRYABLE,"fallback_eligible":failure_type in _FALLBACK,"budget_impact":1,"cooldown_seconds":60 if failure_type in {"rate_limit","resource_exhausted"} else 0,"cache_evidence_reusable":failure_type not in {"semantic_failure","policy_failure"},"manual_approval_required":failure_type in {"unknown_failure","quality_failure","semantic_failure","policy_failure","partial_response"},"network_failure":failure_type in _RETRYABLE or failure_type in {"http_4xx","authentication_failure","invalid_request"}}
