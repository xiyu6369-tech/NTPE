"""RM-7.3.2 P4 — Candidate Deduplication.

Deterministic deduplication based on:
- entity_id + form_type + expected_translation + actual_translation + rule + source_context

Same evidence → same candidate identity.
Different actual translation → different candidate.
Different form type → different candidate.
Different entity → different candidate.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from core.entity_review.models import ReviewCandidate, ReviewStatus


class CandidateDeduplicator:
    """Deterministic candidate deduplication engine.
    
    Uses the candidate_id (already deterministic) as the primary key,
    with additional validation to ensure consistency.
    """
    
    def __init__(self) -> None:
        self._seen: Dict[str, ReviewCandidate] = {}
        self._rejected_ids: Set[str] = set()
        self._accepted_ids: Set[str] = set()

    def deduplicate(self, candidates: List[ReviewCandidate]) -> List[ReviewCandidate]:
        """Deduplicate a list of candidates, keeping the first occurrence.
        
        Returns only candidates with OPEN status that haven't been seen before.
        REJECTED and ACCEPTED candidates are tracked separately.
        """
        result = []
        for candidate in candidates:
            if candidate.candidate_id in self._seen:
                # Already seen - check if status changed
                existing = self._seen[candidate.candidate_id]
                if candidate.status != existing.status:
                    # Status changed - update tracking
                    if candidate.status == ReviewStatus.ACCEPTED:
                        self._accepted_ids.add(candidate.candidate_id)
                        self._rejected_ids.discard(candidate.candidate_id)
                    elif candidate.status == ReviewStatus.REJECTED:
                        self._rejected_ids.add(candidate.candidate_id)
                        self._accepted_ids.discard(candidate.candidate_id)
                    # Update the stored candidate
                    self._seen[candidate.candidate_id] = candidate
                continue

            # New candidate
            self._seen[candidate.candidate_id] = candidate
            
            if candidate.status == ReviewStatus.OPEN:
                result.append(candidate)
            elif candidate.status == ReviewStatus.ACCEPTED:
                self._accepted_ids.add(candidate.candidate_id)
            elif candidate.status == ReviewStatus.REJECTED:
                self._rejected_ids.add(candidate.candidate_id)
            elif candidate.status == ReviewStatus.SUPERSEDED:
                # Superseded candidates are not returned
                pass
        
        return result

    def is_duplicate(self, candidate: ReviewCandidate) -> bool:
        """Check if a candidate is a duplicate of a previously seen one."""
        return candidate.candidate_id in self._seen

    def get_existing(self, candidate_id: str) -> Optional[ReviewCandidate]:
        """Get an existing candidate by ID."""
        return self._seen.get(candidate_id)

    def mark_accepted(self, candidate_id: str) -> bool:
        """Mark a candidate as accepted (tracks for deduplication)."""
        if candidate_id in self._seen:
            self._accepted_ids.add(candidate_id)
            self._rejected_ids.discard(candidate_id)
            return True
        return False

    def mark_rejected(self, candidate_id: str) -> bool:
        """Mark a candidate as rejected (tracks for deduplication)."""
        if candidate_id in self._seen:
            self._rejected_ids.add(candidate_id)
            self._accepted_ids.discard(candidate_id)
            return True
        return False

    def is_accepted(self, candidate_id: str) -> bool:
        """Check if a candidate ID has been accepted."""
        return candidate_id in self._accepted_ids

    def is_rejected(self, candidate_id: str) -> bool:
        """Check if a candidate ID has been rejected."""
        return candidate_id in self._rejected_ids

    def get_all_seen(self) -> Dict[str, ReviewCandidate]:
        """Get all seen candidates (for persistence/inspection)."""
        return dict(self._seen)

    def clear(self) -> None:
        """Clear all tracking state."""
        self._seen.clear()
        self._rejected_ids.clear()
        self._accepted_ids.clear()

    def stats(self) -> Dict[str, int]:
        """Get deduplication statistics."""
        open_count = sum(1 for c in self._seen.values() if c.status == ReviewStatus.OPEN)
        return {
            "total_seen": len(self._seen),
            "open": open_count,
            "accepted": len(self._accepted_ids),
            "rejected": len(self._rejected_ids),
            "superseded": sum(1 for c in self._seen.values() if c.status == ReviewStatus.SUPERSEDED),
        }


class CandidateStore:
    """In-memory candidate store with deduplication.
    
    Can be extended to persist to disk. For P4, in-memory is sufficient
    as canary runs are short-lived.
    """
    
    def __init__(self) -> None:
        self._candidates: Dict[str, ReviewCandidate] = {}
        self._deduplicator = CandidateDeduplicator()

    def add(self, candidate: ReviewCandidate) -> ReviewCandidate:
        """Add a candidate, applying deduplication.
        
        Returns the canonical candidate (either the new one or existing).
        """
        existing = self._deduplicator.get_existing(candidate.candidate_id)
        if existing:
            # Return existing, but update if status is more advanced
            if self._status_order(candidate.status) > self._status_order(existing.status):
                self._candidates[candidate.candidate_id] = candidate
                self._deduplicator._seen[candidate.candidate_id] = candidate
                return candidate
            return existing
        
        # New candidate
        self._candidates[candidate.candidate_id] = candidate
        self._deduplicator._seen[candidate.candidate_id] = candidate
        return candidate

    def add_all(self, candidates: List[ReviewCandidate]) -> List[ReviewCandidate]:
        """Add multiple candidates, returning deduplicated list."""
        result = []
        for c in candidates:
            added = self.add(c)
            if added.candidate_id == c.candidate_id:
                result.append(added)
        return result

    def get(self, candidate_id: str) -> Optional[ReviewCandidate]:
        """Get a candidate by ID."""
        return self._candidates.get(candidate_id)

    def update_status(self, candidate_id: str, new_status: ReviewStatus) -> Optional[ReviewCandidate]:
        """Update candidate status."""
        candidate = self._candidates.get(candidate_id)
        if not candidate:
            return None
        
        updated = candidate.with_status(new_status)
        self._candidates[candidate_id] = updated
        self._deduplicator._seen[candidate_id] = updated
        
        if new_status == ReviewStatus.ACCEPTED:
            self._deduplicator.mark_accepted(candidate_id)
        elif new_status == ReviewStatus.REJECTED:
            self._deduplicator.mark_rejected(candidate_id)
        
        return updated

    def list_open(self) -> List[ReviewCandidate]:
        """List all OPEN candidates."""
        return [c for c in self._candidates.values() if c.status == ReviewStatus.OPEN]

    def list_accepted(self) -> List[ReviewCandidate]:
        """List all ACCEPTED candidates."""
        return [c for c in self._candidates.values() if c.status == ReviewStatus.ACCEPTED]

    def list_rejected(self) -> List[ReviewCandidate]:
        """List all REJECTED candidates."""
        return [c for c in self._candidates.values() if c.status == ReviewStatus.REJECTED]

    def list_all(self) -> List[ReviewCandidate]:
        """List all candidates."""
        return list(self._candidates.values())

    def clear(self) -> None:
        """Clear all candidates."""
        self._candidates.clear()
        self._deduplicator.clear()

    @staticmethod
    def _status_order(status: ReviewStatus) -> int:
        """Order for status precedence."""
        order = {
            ReviewStatus.OPEN: 0,
            ReviewStatus.ACCEPTED: 1,
            ReviewStatus.REJECTED: 2,
            ReviewStatus.SUPERSEDED: 3,
        }
        return order.get(status, 0)

    def stats(self) -> Dict[str, int]:
        """Get store statistics."""
        return self._deduplicator.stats()


# Global store instance (can be replaced for testing)
_global_store: Optional[CandidateStore] = None


def get_global_store() -> CandidateStore:
    """Get the global candidate store."""
    global _global_store
    if _global_store is None:
        _global_store = CandidateStore()
    return _global_store


def set_global_store(store: CandidateStore) -> None:
    """Set the global candidate store (for testing)."""
    global _global_store
    _global_store = store


__all__ = [
    "CandidateDeduplicator",
    "CandidateStore",
    "get_global_store",
    "set_global_store",
]