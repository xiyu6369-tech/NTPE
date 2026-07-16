"""Offline, evidence-bound context and scene memory core (schema 1.0)."""

from .context_selection import select_context_for_translation
from .interoperability import build_character_context_view, link_character_memory, resolve_scene_participant_reference
from .lifecycle import expire_context, reject_context, rollback_context, rollback_scene, supersede_context
from .models import (
    AddDisposition, AddResult, ApprovalStatus, BoundaryType, CharacterContextItem,
    ContextEvidence, ContextMemoryRecord, ContextSelectionResult, ContextType,
    EvidenceType, ExpiryKind, ExpiryPolicy, ParticipantStatus, RecordStatus,
    ResolutionStatus, SceneMemoryRecord, SceneParticipant, SelectedContextItem,
    UnresolvedReference, DEFAULT_CHARACTER_TOKEN_BUDGET, DEFAULT_CONTEXT_TOKEN_BUDGET,
    SCHEMA_VERSION,
)
from .scene_state import (
    add_scene_participant, add_unresolved_reference, remove_scene_participant,
    resolve_reference, transition_chapter, transition_scene, update_scene_state,
)
from .serialization import dumps_context_store, load_context_store, loads_context_store, save_context_store
from .store import (
    ContextMemoryStore, add_or_merge_context, add_scene, create_context_evidence,
    create_context_memory, create_scene_memory, create_unresolved_reference,
)
from .validation import ContextSceneValidationError, validate_context_record, validate_context_store, validate_scene_record

serialize_context_store = dumps_context_store
deserialize_context_store = loads_context_store

__all__ = [name for name in globals() if not name.startswith("_")]
