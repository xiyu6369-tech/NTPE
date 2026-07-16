from __future__ import annotations

from dataclasses import asdict

from .models import SemanticVerificationEvidence
from .serialization import canonical_json
from .validation import sha256_text


def build_evidence(draft_features, polish_features, differences, invariant_fingerprint: str) -> SemanticVerificationEvidence:
    extraction = sha256_text(canonical_json({"draft": asdict(draft_features), "polish": asdict(polish_features)}))
    comparison = sha256_text(canonical_json([asdict(x) for x in differences]))
    return SemanticVerificationEvidence(extraction, comparison, invariant_fingerprint)
