from __future__ import annotations

import hashlib, json
from dataclasses import asdict, replace
from functools import lru_cache

from .models import ProviderProfile, ProviderQualityContract, SCHEMA_VERSION

QUALITY_CONTRACT = ProviderQualityContract("literary-fidelity-zh-hant", "1.0", True, True, True, True, True, True, True, True, "traditional_chinese_corner_quotes", "zh-Hant", "preserve_versioned_work_context", "human_approved_priority", True)


@lru_cache(maxsize=128)
def build_provider_profile_fingerprint(profile: ProviderProfile) -> str:
    value=asdict(profile); value.pop("fingerprint",None)
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()


def create_provider_profile(**values) -> ProviderProfile:
    values=dict(values); values.setdefault("fingerprint","")
    profile=ProviderProfile(**values)
    return replace(profile,fingerprint=build_provider_profile_fingerprint(profile))


def _profile(provider_id, model_id, family, context_limit, output_limit, timeout, json_mode):
    return create_provider_profile(provider_id=provider_id,profile_version="1.0",model_id=model_id,provider_family=family,supported_source_languages=("ko","ja","en"),supported_target_languages=("zh-Hant",),context_limit=context_limit,output_limit=output_limit,supports_streaming=True,supports_json_mode=json_mode,expected_timeout_seconds=timeout,quality_contract_id=QUALITY_CONTRACT.contract_id,quality_contract_version=QUALITY_CONTRACT.version,prompt_contract_id="ntpe-literary-structured",prompt_contract_version="1.0",status="experimental")


NVIDIA_PROFILE=_profile("nvidia-meta-llama-3.2-90b-vision-instruct","meta/llama-3.2-90b-vision-instruct","nvidia",131072,8192,180,True)
GEMINI_PROFILE=_profile("gemini-2.5-flash","gemini-2.5-flash","gemini",1048576,8192,120,True)
PROVIDER_PROFILES=(NVIDIA_PROFILE,GEMINI_PROFILE)


def get_provider_profile(provider_id):
    for profile in PROVIDER_PROFILES:
        if profile.provider_id==provider_id:return profile
    raise LookupError("unknown Provider profile")
