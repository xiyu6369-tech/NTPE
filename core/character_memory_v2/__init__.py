"""Pure-offline Character Memory V2 core.

This package has no Provider, Runtime, Prompt, translation pipeline, Resume,
Output Assembly, TIC production API, CLI, or Web UI dependency.
"""

from .lifecycle import approve_memory, expire_memory, reject_memory, rollback_memory, supersede_memory
from .models import (
    DEFAULT_PROMPT_TOKEN_BUDGET,
    MAX_EVIDENCE_EXCERPT_CHARS,
    SCHEMA_VERSION,
    AddDisposition,
    AddResult,
    ApprovalMetadata,
    ApprovalStatus,
    ConflictRecord,
    Evidence,
    EvidenceType,
    ExpiryKind,
    ExpiryPolicy,
    FactType,
    MemoryRecord,
    MemoryStatus,
    PromptMemoryItem,
    SelectionResult,
)
from .selection import estimate_memory_tokens, select_prompt_eligible_memories
from .serialization import deserialize_memory_store, serialize_memory_store
from .store import MemoryStore, add_or_merge_memory, create_evidence, create_memory
from .validation import CharacterMemoryValidationError, validate_memory_store, validate_record


__all__ = [
    "SCHEMA_VERSION", "DEFAULT_PROMPT_TOKEN_BUDGET", "MAX_EVIDENCE_EXCERPT_CHARS",
    "AddDisposition", "AddResult", "ApprovalMetadata", "ApprovalStatus", "CharacterMemoryValidationError",
    "ConflictRecord", "Evidence", "EvidenceType", "ExpiryKind", "ExpiryPolicy", "FactType",
    "MemoryRecord", "MemoryStatus", "MemoryStore", "PromptMemoryItem", "SelectionResult",
    "add_or_merge_memory", "approve_memory", "create_evidence", "create_memory", "deserialize_memory_store",
    "estimate_memory_tokens", "expire_memory", "reject_memory", "rollback_memory",
    "select_prompt_eligible_memories", "serialize_memory_store", "supersede_memory",
    "validate_memory_store", "validate_record",
]
