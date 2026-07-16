from __future__ import annotations

import re
from .classification import FAILURE_TYPES
from .models import *
from .provider_profiles import PROVIDER_PROFILES, build_provider_profile_fingerprint

HEALTH_STATES=("healthy","degraded","unavailable","unknown","rate_limited","timeout_prone","quality_unverified")
MODES=("single_pass","dual_pass","selective_polish")


def validate_provider_profile(profile:ProviderProfile)->None:
    if profile.profile_version!="1.0" or profile.status not in {"experimental","active","deprecated","frozen"}:raise ValueError("invalid provider profile")
    if not profile.provider_id or not profile.model_id or profile.context_limit<=0 or profile.output_limit<=0:raise ValueError("invalid provider profile")
    if build_provider_profile_fingerprint(profile)!=profile.fingerprint:raise ValueError("provider fingerprint mismatch")
    text=repr(profile).lower()
    if any(x in text for x in ("api_key","authorization","credential","?key=","raw_request","raw_response")):raise ValueError("secret-bearing profile")


def validate_budget(budget:ProviderRequestBudget)->None:
    if any(getattr(budget,name)<0 for name in budget.__dataclass_fields__):raise ValueError("negative budget")
    if budget.maximum_requests_per_chunk>budget.maximum_requests_per_document:raise ValueError("invalid request budget")


def validate_routing_input(item:ProviderRoutingInput)->None:
    validate_budget(item.request_budget)
    if item.source_language not in {"ko","ja","en"} or item.target_language!="zh-Hant":raise ValueError("unsupported language pair")
    if item.translation_mode not in MODES:raise ValueError("invalid translation mode")
    if not item.semantic_verification_available:raise ValueError("semantic verification unavailable")
    if any(x<0 for x in (item.estimated_input_tokens,item.estimated_output_tokens,item.current_requests,item.current_document_requests,item.current_retry_requests,item.current_fallback_requests,item.current_polish_requests,item.current_input_tokens,item.current_output_tokens,item.current_wall_clock_seconds)):raise ValueError("negative usage")
    if any(state not in HEALTH_STATES for state in item.provider_health_evidence.values()):raise ValueError("unknown provider health state")
    for evidence in item.provider_failure_history:
        if evidence.failure_type not in FAILURE_TYPES:raise ValueError("unknown failure evidence")


def reject_unsafe(value)->None:
    text=repr(value).lower()
    if "../" in text or "..\\" in text:raise ValueError("path traversal rejected")
    if any(x in text for x in ("authorization: bearer","api_key=","private key","raw_provider_request","raw_provider_response","?key=")):raise ValueError("unsafe provider payload")
