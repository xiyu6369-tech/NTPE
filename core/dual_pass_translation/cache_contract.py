from __future__ import annotations
import hashlib,json
from dataclasses import asdict
from .models import *
def _canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)
def _key(value):return hashlib.sha256(_canonical(asdict(value)).encode()).hexdigest()
def build_draft_cache_identity(*,source_hash,prompt_identity,draft_policy_version,character_memory_selection_fingerprint,context_scene_selection_fingerprint,glossary_fingerprint):return DraftCacheIdentity(source_hash,prompt_identity,draft_policy_version,character_memory_selection_fingerprint,context_scene_selection_fingerprint,glossary_fingerprint)
def build_polish_cache_identity(*,draft_hash,polish_policy_version,polish_scope_hash,semantic_policy_version,character_memory_selection_fingerprint,context_scene_selection_fingerprint,glossary_fingerprint):return PolishCacheIdentity(draft_hash,polish_policy_version,polish_scope_hash,semantic_policy_version,character_memory_selection_fingerprint,context_scene_selection_fingerprint,glossary_fingerprint)
def draft_cache_key(identity):return _key(identity)
def polish_cache_key(identity):return _key(identity)
def compare_polish_cache_identity(cached,current):
    if cached.draft_hash!=current.draft_hash:return {"usable":False,"reason":"draft_hash_changed","reverification_required":True}
    if cached.polish_policy_version!=current.polish_policy_version:return {"usable":False,"reason":"polish_policy_changed","reverification_required":True}
    if cached.semantic_policy_version!=current.semantic_policy_version:return {"usable":False,"reason":"semantic_policy_changed","reverification_required":True}
    if cached.polish_scope_hash!=current.polish_scope_hash:return {"usable":False,"reason":"polish_scope_changed","reverification_required":True}
    if cached.character_memory_selection_fingerprint!=current.character_memory_selection_fingerprint or cached.context_scene_selection_fingerprint!=current.context_scene_selection_fingerprint:return {"usable":False,"reason":"memory_selection_changed","reverification_required":True}
    if cached.glossary_fingerprint!=current.glossary_fingerprint:return {"usable":False,"reason":"glossary_changed","reverification_required":True}
    return {"usable":True,"reason":"identity_match","reverification_required":False}
def build_final_output_identity(*,rollback_decision,draft_identity,polish_identity,semantic_policy_version,verification_status):
    if rollback_decision.action==RollbackAction.ACCEPT_POLISH:selected="polish";polish_key=polish_cache_key(polish_identity)
    elif rollback_decision.action==RollbackAction.ROLLBACK_TO_DRAFT:selected="draft";polish_key=None
    else:selected="blocked";polish_key=None
    return FinalOutputIdentity(selected,rollback_decision.selected_hash or "",draft_cache_key(draft_identity),polish_key,semantic_policy_version,verification_status)
