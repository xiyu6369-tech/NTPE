from __future__ import annotations
import hashlib, json, unicodedata
from typing import Any, Mapping
from .models import CacheIdentity


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_text(value: str) -> str: return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_source(value: str) -> str:
    return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))


def fingerprint_value(value: Any) -> str: return sha256_text(canonical_json(value) if not isinstance(value,str) else value)


def create_cache_identity(*, source_text:str, prompt:str, system_prompt:str, policy:Any, context_selection:Any, glossary:Any,
    character_memory_selection_fingerprint:str, context_scene_selection_fingerprint:str, language_profile_id:str,
    language_profile_version:str, source_language:str, target_language:str, provider_id:str, model_id:str,
    provider_request_profile:Any, generation_settings:Any, quality_policy_id:str, quality_policy_version:str,
    translation_engine_version:str, chunk_index:int, document_id:str, chunking_strategy_id:str,
    chunking_strategy_version:str, context_token_budget:int) -> CacheIdentity:
    return CacheIdentity(sha256_text(source_text),sha256_text(normalize_source(source_text)),fingerprint_value(prompt),fingerprint_value(system_prompt),fingerprint_value(policy),fingerprint_value(context_selection),fingerprint_value(glossary),character_memory_selection_fingerprint,context_scene_selection_fingerprint,language_profile_id,language_profile_version,source_language,target_language,provider_id,model_id,fingerprint_value(provider_request_profile),fingerprint_value(generation_settings),quality_policy_id,quality_policy_version,translation_engine_version,chunk_index,document_id,chunking_strategy_id,chunking_strategy_version,context_token_budget)


def cache_key_for_identity(identity: CacheIdentity) -> str: return sha256_text(canonical_json(identity.to_dict()))
