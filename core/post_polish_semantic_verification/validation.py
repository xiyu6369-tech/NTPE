from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any

from .models import SemanticInvariant, SemanticVerificationInput
from .policy import INVARIANT_TYPES

HASH_RE = re.compile(r"^[0-9a-f]{64}$")
ORIGINS = {"source_observation", "draft_verification", "human_approved", "tic_regression", "glossary", "character_memory", "context_scene_memory", "rule_derived"}


def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def sha256_text(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()


def validate_input(value: SemanticVerificationInput) -> None:
    for name in ("source_text", "verified_draft_text", "polish_text", "verification_id", "document_id"):
        if not isinstance(getattr(value, name), str) or not getattr(value, name).strip():
            raise ValueError(f"missing required input: {name}")
    for text_name, hash_name in (("source_text", "source_hash"), ("verified_draft_text", "verified_draft_hash"), ("polish_text", "polish_hash")):
        if sha256_text(getattr(value, text_name)) != getattr(value, hash_name):
            raise ValueError(f"{hash_name} mismatch")
    scope = value.polish_scope
    if not isinstance(scope, dict) or scope.get("scope_type") not in {"full_chunk", "sentence_span", "paragraph_span", "dialogue_span"}:
        raise ValueError("invalid scope")
    if scope.get("scope_type") != "full_chunk":
        required = {"draft_before", "draft_selected", "draft_after", "polish_before", "polish_selected", "polish_after"}
        if not required <= set(scope):
            raise ValueError("malformed selective scope")
        if scope["draft_before"] != scope["polish_before"] or scope["draft_after"] != scope["polish_after"]:
            raise ValueError("out of scope change")
        if scope["draft_before"] + scope["draft_selected"] + scope["draft_after"] != value.verified_draft_text:
            raise ValueError("draft span mismatch")
        if scope["polish_before"] + scope["polish_selected"] + scope["polish_after"] != value.polish_text:
            raise ValueError("polish span mismatch")


def validate_invariant(item: SemanticInvariant) -> None:
    if item.invariant_type not in INVARIANT_TYPES or not item.invariant_id:
        raise ValueError("malformed invariant")
    if not 0 <= item.confidence <= 1 or item.origin not in ORIGINS:
        raise ValueError("malformed invariant")
    if item.approval_status not in {"observed", "unresolved", "multiple_candidates", "human_approved", "conflicting"}:
        raise ValueError("malformed invariant")


def reject_unsafe_payload(value: Any) -> None:
    text = repr(value)
    lowered = text.lower()
    if "../" in text or "..\\" in text:
        raise ValueError("path traversal rejected")
    forbidden = ("authorization: bearer", "private key", "raw_provider_request", "raw_provider_response")
    if any(token in lowered for token in forbidden):
        raise ValueError("secret-like or provider payload rejected")
