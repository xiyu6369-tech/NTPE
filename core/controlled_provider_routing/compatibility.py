from __future__ import annotations

from .models import ProviderCompatibilityResult, ProviderProfile, ProviderRoutingInput
from .validation import validate_provider_profile, validate_routing_input


def evaluate_provider_compatibility(item:ProviderRoutingInput,profile:ProviderProfile,*,required_quality_contract_id:str,required_quality_contract_version:str,required_prompt_contract_id:str,required_prompt_contract_version:str)->ProviderCompatibilityResult:
    validate_routing_input(item);validate_provider_profile(profile);reasons=[];manual=False
    if item.source_language not in profile.supported_source_languages or item.target_language not in profile.supported_target_languages:reasons.append("unsupported_language_pair")
    if item.estimated_input_tokens+item.estimated_output_tokens>profile.context_limit:reasons.append("context_limit_exceeded")
    if item.estimated_output_tokens>profile.output_limit:reasons.append("output_limit_exceeded")
    quality=profile.quality_contract_id==required_quality_contract_id and profile.quality_contract_version==required_quality_contract_version
    prompt=profile.prompt_contract_id==required_prompt_contract_id and profile.prompt_contract_version==required_prompt_contract_version
    if not quality:reasons.append("quality_contract_incompatible")
    if not prompt:reasons.append("prompt_contract_incompatible")
    if not item.semantic_verification_available:reasons.append("semantic_verification_unavailable")
    health=item.provider_health_evidence.get(profile.provider_id,"unknown")
    if health in {"unavailable","rate_limited","quality_unverified"}:reasons.append("provider_health_"+health)
    elif health=="unknown":manual=True;reasons.append("provider_health_unknown")
    if item.translation_mode=="dual_pass" and health in {"degraded","timeout_prone"}:reasons.append("full_dual_pass_forbidden_for_degraded_provider")
    hard=[x for x in reasons if x!="provider_health_unknown"]
    return ProviderCompatibilityResult("manual_review_required" if manual and not hard else "compatible" if not hard else "incompatible",not hard and not manual,tuple(reasons),manual,quality,prompt)
