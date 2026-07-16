from __future__ import annotations

from .models import SemanticInvariant
from .validation import sha256_text, validate_invariant


def create_semantic_invariant(*, invariant_id: str, invariant_type: str, source_evidence, draft_evidence, expected_value, scope: str = "full_chunk", confidence: float = 1.0, approval_status: str = "observed", blocking: bool = True, origin: str = "rule_derived") -> SemanticInvariant:
    item = SemanticInvariant(invariant_id, invariant_type, source_evidence, draft_evidence, expected_value, scope, confidence, approval_status, blocking, origin)
    validate_invariant(item)
    return item


def invariant_fingerprint(invariants: tuple[SemanticInvariant, ...]) -> str:
    from .serialization import canonical_json
    return sha256_text(canonical_json([item.__dict__ for item in sorted(invariants, key=lambda x: x.invariant_id)]))
