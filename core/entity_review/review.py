"""RM-7.3.2 P4 — Review API.

Minimal review lifecycle:
    review(candidate_id, ACCEPT)  → creates KnowledgeEvolutionCandidate
    review(candidate_id, REJECT)  → records rejection, no Knowledge Evolution

ACCEPT ≠ auto-modify knowledge base.
ACCEPT = "human confirms this has Knowledge Evolution value".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.entity_review.models import (
    KnowledgeEvolutionCandidate,
    ReviewCandidate,
    ReviewStatus,
)
from core.entity_review.dedup import CandidateStore, get_global_store


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReviewError(Exception):
    """Review operation error."""
    pass


class CandidateNotFoundError(ReviewError):
    """Candidate not found."""
    pass


class InvalidTransitionError(ReviewError):
    """Invalid status transition."""
    pass


@dataclass(frozen=True)
class ReviewAction:
    """Record of a review action for audit trail."""
    candidate_id: str
    action: ReviewStatus
    reviewer: str = "human"
    reason: str = ""
    metadata: Dict[str, Any] = None
    timestamp: str = None

    def __post_init__(self):
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", utc_now_iso())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "action": self.action.value,
            "reviewer": self.reviewer,
            "reason": self.reason,
            "metadata": dict(self.metadata),
            "timestamp": self.timestamp,
        }


class ReviewEngine:
    """Review lifecycle engine.
    
    Manages the OPEN → ACCEPTED/REJECTED transitions.
    Produces KnowledgeEvolutionCandidate ONLY on ACCEPT.
    """
    
    def __init__(self, store: Optional[CandidateStore] = None) -> None:
        self._store = store or get_global_store()
        self._actions: List[ReviewAction] = []

    def accept(
        self,
        candidate_id: str,
        reviewer: str = "human",
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeEvolutionCandidate:
        """Accept a candidate — creates KnowledgeEvolutionCandidate.
        
        This is the ONLY way to create a KnowledgeEvolutionCandidate.
        Does NOT modify glossary/knowledge base directly.
        
        Args:
            candidate_id: ID of candidate to accept
            reviewer: Who is accepting (default: "human")
            reason: Why this was accepted
            metadata: Additional metadata
        
        Returns:
            KnowledgeEvolutionCandidate ready for Knowledge Evolution pipeline
        
        Raises:
            CandidateNotFoundError: If candidate doesn't exist
            InvalidTransitionError: If candidate is not OPEN
        """
        candidate = self._store.get(candidate_id)
        if not candidate:
            raise CandidateNotFoundError(f"Candidate {candidate_id} not found")
        
        if candidate.status != ReviewStatus.OPEN:
            raise InvalidTransitionError(
                f"Cannot accept candidate in status {candidate.status.value}, must be OPEN"
            )
        
        # Update status
        updated = self._store.update_status(candidate_id, ReviewStatus.ACCEPTED)
        if not updated:
            raise CandidateNotFoundError(f"Candidate {candidate_id} not found after update")
        
        # Record action
        action = ReviewAction(
            candidate_id=candidate_id,
            action=ReviewStatus.ACCEPTED,
            reviewer=reviewer,
            reason=reason,
            metadata=metadata or {},
        )
        self._actions.append(action)
        
        # Create Knowledge Evolution Candidate
        ke_candidate = KnowledgeEvolutionCandidate.from_review_candidate(updated)
        return ke_candidate

    def reject(
        self,
        candidate_id: str,
        reviewer: str = "human",
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReviewCandidate:
        """Reject a candidate — records rejection, NO Knowledge Evolution.
        
        Reject means: this mismatch is not a learning opportunity.
        Examples: contextual exception, deliberate variant, known allowed form.
        
        Args:
            candidate_id: ID of candidate to reject
            reviewer: Who is rejecting (default: "human")
            reason: Why this was rejected
            metadata: Additional metadata
        
        Returns:
            The updated REJECTED ReviewCandidate
        
        Raises:
            CandidateNotFoundError: If candidate doesn't exist
            InvalidTransitionError: If candidate is not OPEN
        """
        candidate = self._store.get(candidate_id)
        if not candidate:
            raise CandidateNotFoundError(f"Candidate {candidate_id} not found")
        
        if candidate.status != ReviewStatus.OPEN:
            raise InvalidTransitionError(
                f"Cannot reject candidate in status {candidate.status.value}, must be OPEN"
            )
        
        # Update status
        updated = self._store.update_status(candidate_id, ReviewStatus.REJECTED)
        if not updated:
            raise CandidateNotFoundError(f"Candidate {candidate_id} not found after update")
        
        # Record action
        action = ReviewAction(
            candidate_id=candidate_id,
            action=ReviewStatus.REJECTED,
            reviewer=reviewer,
            reason=reason,
            metadata=metadata or {},
        )
        self._actions.append(action)
        
        return updated

    def supersede(
        self,
        candidate_id: str,
        reviewer: str = "human",
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReviewCandidate:
        """Mark a candidate as superseded by another candidate.
        
        Used when a newer candidate covers the same issue.
        """
        candidate = self._store.get(candidate_id)
        if not candidate:
            raise CandidateNotFoundError(f"Candidate {candidate_id} not found")
        
        updated = self._store.update_status(candidate_id, ReviewStatus.SUPERSEDED)
        if not updated:
            raise CandidateNotFoundError(f"Candidate {candidate_id} not found after update")
        
        action = ReviewAction(
            candidate_id=candidate_id,
            action=ReviewStatus.SUPERSEDED,
            reviewer=reviewer,
            reason=reason,
            metadata=metadata or {},
        )
        self._actions.append(action)
        
        return updated

    def get_candidate(self, candidate_id: str) -> Optional[ReviewCandidate]:
        """Get a candidate by ID."""
        return self._store.get(candidate_id)

    def list_open(self) -> List[ReviewCandidate]:
        """List all OPEN candidates pending review."""
        return self._store.list_open()

    def list_accepted(self) -> List[ReviewCandidate]:
        """List all ACCEPTED candidates."""
        return self._store.list_accepted()

    def list_rejected(self) -> List[ReviewCandidate]:
        """List all REJECTED candidates."""
        return self._store.list_rejected()

    def list_all(self) -> List[ReviewCandidate]:
        """List all candidates."""
        return self._store.list_all()

    def get_actions(self, candidate_id: Optional[str] = None) -> List[ReviewAction]:
        """Get review actions, optionally filtered by candidate."""
        if candidate_id:
            return [a for a in self._actions if a.candidate_id == candidate_id]
        return list(self._actions)

    def get_accepted_ke_candidates(self) -> List[KnowledgeEvolutionCandidate]:
        """Get all KnowledgeEvolutionCandidates from accepted reviews."""
        accepted = self._store.list_accepted()
        return [KnowledgeEvolutionCandidate.from_review_candidate(c) for c in accepted]

    def stats(self) -> Dict[str, int]:
        """Get review statistics."""
        store_stats = self._store.stats()
        return {
            **store_stats,
            "total_actions": len(self._actions),
            "accept_actions": sum(1 for a in self._actions if a.action == ReviewStatus.ACCEPTED),
            "reject_actions": sum(1 for a in self._actions if a.action == ReviewStatus.REJECTED),
        }


# Module-level convenience functions using global store
_global_engine: Optional[ReviewEngine] = None


def get_review_engine() -> ReviewEngine:
    """Get the global review engine."""
    global _global_engine
    if _global_engine is None:
        _global_engine = ReviewEngine()
    return _global_engine


def set_review_engine(engine: ReviewEngine) -> None:
    """Set the global review engine (for testing)."""
    global _global_engine
    _global_engine = engine


def reset_review_engine() -> None:
    """Reset the global review engine (for testing)."""
    global _global_engine
    _global_engine = None


def review(candidate_id: str, action: ReviewStatus, reviewer: str = "human",
           reason: str = "", metadata: Optional[Dict[str, Any]] = None) -> Any:
    """Main review API entry point.
    
    Args:
        candidate_id: Candidate to review
        action: ACCEPT or REJECT (or SUPERSEDED)
        reviewer: Who is reviewing
        reason: Why
        metadata: Additional data
    
    Returns:
        KnowledgeEvolutionCandidate if ACCEPT, ReviewCandidate if REJECT/SUPERSEDED
    
    Raises:
        ReviewError: On invalid operation
    """
    engine = get_review_engine()
    
    if action == ReviewStatus.ACCEPTED:
        return engine.accept(candidate_id, reviewer, reason, metadata)
    elif action == ReviewStatus.REJECTED:
        return engine.reject(candidate_id, reviewer, reason, metadata)
    elif action == ReviewStatus.SUPERSEDED:
        return engine.supersede(candidate_id, reviewer, reason, metadata)
    else:
        raise ReviewError(f"Unsupported review action: {action.value}")


__all__ = [
    "ReviewError",
    "CandidateNotFoundError",
    "InvalidTransitionError",
    "ReviewAction",
    "ReviewEngine",
    "get_review_engine",
    "set_review_engine",
    "reset_review_engine",
    "review",
]