"""RM-7.3.2 P4 — Entity Consistency Review Module.

Detect → Report → Review → Accept → Learn

No auto-learning. No provider. No network. No translation engine dependencies.

Main components:
- models: ReviewCandidate, Evidence, KnowledgeEvolutionCandidate, enums
- candidate: Factory to create ReviewCandidate from EntityMismatch
- dedup: Deterministic deduplication (same evidence = same candidate_id)
- review: Review lifecycle API (accept/reject) → KnowledgeEvolutionCandidate
- exporter: Bridge to Knowledge Evolution pipeline

Usage:
    from core.entity_review import (
        create_candidate_from_mismatch,
        review,
        ReviewStatus,
        KnowledgeEvolutionExporter,
    )
"""

from .models import (
    CandidateOrigin,
    ReviewStatus,
    FormType,
    Evidence,
    ReviewCandidate,
    KnowledgeEvolutionCandidate,
)
from .candidate import (
    create_candidate_from_mismatch,
    create_candidates_from_mismatches,
)
from .dedup import (
    CandidateDeduplicator,
    CandidateStore,
    get_global_store,
    set_global_store,
)
from .review import (
    ReviewError,
    CandidateNotFoundError,
    InvalidTransitionError,
    ReviewAction,
    ReviewEngine,
    get_review_engine,
    set_review_engine,
    reset_review_engine,
    review,
)
from .exporter import (
    KnowledgeEvolutionExporter,
    ReviewReportExporter,
    export_to_knowledge_evolution,
)

__all__ = [
    # Models
    "CandidateOrigin",
    "ReviewStatus",
    "FormType",
    "Evidence",
    "ReviewCandidate",
    "KnowledgeEvolutionCandidate",
    # Candidate factory
    "create_candidate_from_mismatch",
    "create_candidates_from_mismatches",
    # Deduplication
    "CandidateDeduplicator",
    "CandidateStore",
    "get_global_store",
    "set_global_store",
    # Review API
    "ReviewError",
    "CandidateNotFoundError",
    "InvalidTransitionError",
    "ReviewAction",
    "ReviewEngine",
    "get_review_engine",
    "set_review_engine",
    "reset_review_engine",
    "review",
    # Exporter
    "KnowledgeEvolutionExporter",
    "ReviewReportExporter",
    "export_to_knowledge_evolution",
]