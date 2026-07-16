from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any,Mapping
SCHEMA_VERSION="1.0"
class TranslationMode(str,Enum):SINGLE_PASS="single_pass";DUAL_PASS="dual_pass";SELECTIVE_POLISH="selective_polish";BLOCKED="blocked"
class QualityStatus(str,Enum):PASSED="passed";PASSED_WITH_NONBLOCKING_ISSUES="passed_with_nonblocking_issues";FAILED="failed";NOT_EVALUATED="not_evaluated";INSUFFICIENT_EVIDENCE="insufficient_evidence";INVALID="invalid"
class SemanticStatus(str,Enum):PASSED="passed";FAILED="failed";INSUFFICIENT_EVIDENCE="insufficient_evidence";INVALID="invalid"
class ArtifactStatus(str,Enum):PREPARED="prepared";VERIFIED="verified";FAILED="failed";INVALID="invalid";REJECTED="rejected";FINAL="final";ROLLED_BACK="rolled_back"
class PolishScopeType(str,Enum):FULL_CHUNK="full_chunk";SENTENCE_SPAN="sentence_span";PARAGRAPH_SPAN="paragraph_span";DIALOGUE_SPAN="dialogue_span";NONE="none"
class TriggerType(str,Enum):TRANSLATIONESE="translationese";AWKWARD_WORD_ORDER="awkward_word_order";DIALOGUE_NATURALNESS="dialogue_naturalness";VOICE_INCONSISTENCY="voice_inconsistency";REGISTER_MISMATCH="register_mismatch";ERA_CONTEXT_MISMATCH="era_context_mismatch";PUNCTUATION_STYLE="punctuation_style";REPETITION_NONSEMANTIC="repetition_nonsemantic";LITERAL_IDIOM="literal_idiom";HUMAN_REQUESTED="human_requested";NO_TRIGGER="no_trigger"
class Severity(str,Enum):INFO="info";NONBLOCKING="nonblocking";BLOCKING="blocking";CRITICAL="critical"
class VerificationStatus(str,Enum):PASSED="passed";FAILED="failed";INSUFFICIENT_EVIDENCE="insufficient_evidence";INVALID="invalid"
class RollbackAction(str,Enum):ACCEPT_POLISH="accept_polish";ROLLBACK_TO_DRAFT="rollback_to_draft";BLOCK_OUTPUT="block_output";MANUAL_REVIEW_REQUIRED="manual_review_required"
class ProviderHealth(str,Enum):HEALTHY="provider_healthy";DEGRADED="provider_degraded";UNAVAILABLE="provider_unavailable";UNKNOWN="unknown"
@dataclass(frozen=True)
class DraftTranslationResult:
    draft_id:str;document_id:str;chunk_index:int;source_hash:str;prompt_identity:str;source_language:str;target_language:str;draft_text:str;draft_hash:str;quality_status:QualityStatus;quality_evidence:tuple[Mapping[str,Any],...];semantic_status:SemanticStatus;created_at:str;version:int;status:ArtifactStatus;semantic_invariants:Mapping[str,Any];partial:bool=False;timeout:bool=False;cancelled:bool=False;corrupt:bool=False
@dataclass(frozen=True)
class PolishScope:
    scope_type:PolishScopeType;start_identifier:str|None;end_identifier:str|None;original_draft_hash:str;selected_text_hash:str;surrounding_context_hash:str;outside_before_hash:str|None=None;outside_after_hash:str|None=None
@dataclass(frozen=True)
class PolishCandidate:
    polish_id:str;draft_id:str;source_hash:str;draft_hash:str;polish_text:str;polish_hash:str;polish_scope:PolishScope;polish_reason:str;verification_status:VerificationStatus;semantic_issues:tuple["SemanticIssue",...];created_at:str;version:int;status:ArtifactStatus;semantic_invariants:Mapping[str,Any];outside_before_hash:str|None=None;outside_after_hash:str|None=None
@dataclass(frozen=True)
class PolishRequestContract:
    source_hash:str;verified_draft_hash:str;polish_scope_hash:str;character_memory_selection_fingerprint:str;context_scene_selection_fingerprint:str;glossary_fingerprint:str;quality_policy_version:str;polish_policy_version:str;prepare_only:bool=True;executed:bool=False
@dataclass(frozen=True)
class PolishTrigger:
    trigger_id:str;trigger_type:TriggerType;evidence:tuple[Mapping[str,Any],...];confidence:float;severity:Severity;scope:PolishScope;estimated_quality_value:float;estimated_cost:int;eligible:bool
@dataclass(frozen=True)
class SemanticIssue:
    issue_id:str;issue_type:str;severity:Severity;source_evidence:str;draft_evidence:str;polish_evidence:str;scope:str;blocking:bool;confidence:float;resolution:str
@dataclass(frozen=True)
class SemanticVerificationResult:
    status:VerificationStatus;issues:tuple[SemanticIssue,...];checked_invariants:tuple[str,...];policy_version:str;candidate_id:str;blocking_issue_count:int;prototype_kind:str="offline structural semantic verification prototype"
@dataclass(frozen=True)
class ProviderCostEstimate:
    request_count:int;input_tokens:int;output_tokens:int;total_tokens:int;estimated_latency:float;timeout_risk:float;retry_risk:float;cache_reuse_possible:bool;worst_case_requests:int;maximum_polish_requests_per_chunk:int=1
@dataclass(frozen=True)
class DualPassDecision:
    mode:TranslationMode;decision:str;reasons:tuple[str,...];triggered_rules:tuple[str,...];estimated_requests:int;estimated_input_tokens:int;estimated_output_tokens:int;estimated_timeout_risk:float;fallback_policy:str
@dataclass(frozen=True)
class RollbackDecision:
    action:RollbackAction;reason:str;selected_text:str|None;selected_hash:str|None;draft_id:str;polish_id:str|None;polish_evidence_preserved:bool
@dataclass(frozen=True)
class DualPassExecutionPlan:
    mode:TranslationMode;draft_required:bool;polish_required:bool;polish_scope:PolishScope|None;verification_required:bool;rollback_available:bool;estimated_requests:int;estimated_tokens:int;maximum_requests:int;cache_candidates:tuple[str,...];blocked_reasons:tuple[str,...];prepare_only:bool;executed:bool
@dataclass(frozen=True)
class DualPassExecutionEvidence:
    plan_fingerprint:str;executed:bool;provider_executed:bool;network_requests:int;new_translation_generated:bool;events:tuple[Mapping[str,Any],...]
@dataclass(frozen=True)
class DraftCacheIdentity:
    source_hash:str;prompt_identity:str;draft_policy_version:str;character_memory_selection_fingerprint:str;context_scene_selection_fingerprint:str;glossary_fingerprint:str
@dataclass(frozen=True)
class PolishCacheIdentity:
    draft_hash:str;polish_policy_version:str;polish_scope_hash:str;semantic_policy_version:str;character_memory_selection_fingerprint:str;context_scene_selection_fingerprint:str;glossary_fingerprint:str
@dataclass(frozen=True)
class FinalOutputIdentity:
    selected_kind:str;selected_hash:str;draft_cache_key:str;polish_cache_key:str|None;semantic_policy_version:str;verification_status:VerificationStatus
