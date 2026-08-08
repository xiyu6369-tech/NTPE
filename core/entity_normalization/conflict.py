"""RM-7.3 Conflict Detection & Resolution.

Detects and resolves conflicts between candidate translations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .models import (
    CanonicalEntity,
    ConflictRecord,
    ConflictSeverity,
    EntityType,
    ResolutionSource,
)


@dataclass(frozen=True)
class ConflictCandidate:
    """A candidate translation with its source priority."""
    translation: str
    source: ResolutionSource
    confidence: float = 1.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})


class ConflictDetector:
    """Detects conflicts between translation candidates."""

    def __init__(self):
        self._conflicts: List[ConflictRecord] = []

    def detect(
        self,
        source: str,
        entity_type: EntityType,
        candidates: List[ConflictCandidate]
    ) -> List[ConflictRecord]:
        """Detect conflicts among candidates for the same source.

        Args:
            source: Source text (Korean)
            entity_type: Type of entity
            candidates: List of candidate translations with sources

        Returns:
            List of ConflictRecord (empty if no conflict)
        """
        if len(candidates) <= 1:
            return []

        # Get unique translations
        unique_translations = []
        seen = set()
        for c in candidates:
            if c.translation not in seen:
                unique_translations.append(c.translation)
                seen.add(c.translation)

        if len(unique_translations) <= 1:
            return []

        # Determine severity
        severity = self._calculate_severity(candidates, unique_translations)

        conflict = ConflictRecord(
            source=source,
            entity_type=entity_type,
            candidates=unique_translations,
            severity=severity,
            metadata={"candidate_count": len(candidates)},
        )

        self._conflicts.append(conflict)
        return [conflict]

    def _calculate_severity(
        self,
        candidates: List[ConflictCandidate],
        unique_translations: List[str]
    ) -> ConflictSeverity:
        """Calculate conflict severity."""
        # High severity if USER and RUNTIME disagree
        has_user = any(c.source == ResolutionSource.USER for c in candidates)
        has_runtime = any(c.source == ResolutionSource.RUNTIME for c in candidates)

        if has_user and has_runtime:
            user_translations = {c.translation for c in candidates if c.source == ResolutionSource.USER}
            runtime_translations = {c.translation for c in candidates if c.source == ResolutionSource.RUNTIME}
            if user_translations != runtime_translations:
                return ConflictSeverity.HIGH

        # High severity if multiple high-priority sources disagree
        high_priority = [c for c in candidates if c.source in (ResolutionSource.USER, ResolutionSource.RUNTIME)]
        if len(high_priority) >= 2:
            translations = {c.translation for c in high_priority}
            if len(translations) > 1:
                return ConflictSeverity.HIGH

        # Medium severity for LEARNING vs AUTO conflicts
        return ConflictSeverity.MEDIUM

    def get_all_conflicts(self) -> List[ConflictRecord]:
        return list(self._conflicts)

    def clear(self) -> None:
        self._conflicts.clear()


class ConflictResolver:
    """Resolves conflicts using priority hierarchy: USER > RUNTIME > LEARNING > AUTO."""

    def __init__(self):
        self._resolutions: Dict[str, ConflictRecord] = {}  # source -> resolved ConflictRecord

    def resolve(self, conflict: ConflictRecord) -> ConflictRecord:
        """Resolve a conflict using priority hierarchy.

        The highest priority source wins.
        """
        # This method expects the conflict to have candidates with source info in metadata
        # For now, we'll use a simplified resolution based on the first candidate
        # In practice, the caller should provide candidate sources

        # Default: first candidate wins (should be overridden by caller with proper priority)
        resolution = conflict.candidates[0] if conflict.candidates else None

        if resolution:
            resolved = ConflictRecord(
                source=conflict.source,
                entity_type=conflict.entity_type,
                candidates=conflict.candidates,
                severity=conflict.severity,
                resolution=resolution,
                resolution_source=ResolutionSource.AUTO,  # Will be updated by caller
                metadata=conflict.metadata,
                created_at=conflict.created_at,
            )
        else:
            resolved = conflict

        self._resolutions[conflict.source] = resolved
        return resolved

    def resolve_with_priority(
        self,
        conflict: ConflictRecord,
        candidates: List[ConflictCandidate]
    ) -> ConflictRecord:
        """Resolve conflict with explicit candidate priorities."""
        # Sort by priority (USER first)
        priority_order = {
            ResolutionSource.USER: 0,
            ResolutionSource.RUNTIME: 1,
            ResolutionSource.LEARNING: 2,
            ResolutionSource.AUTO: 3,
        }

        sorted_candidates = sorted(candidates, key=lambda c: priority_order.get(c.source, 99))

        if not sorted_candidates:
            return conflict

        winner = sorted_candidates[0]

        resolved = ConflictRecord(
            source=conflict.source,
            entity_type=conflict.entity_type,
            candidates=conflict.candidates,
            severity=conflict.severity,
            resolution=winner.translation,
            resolution_source=winner.source,
            metadata={**conflict.metadata, "resolution_confidence": winner.confidence},
            created_at=conflict.created_at,
        )

        self._resolutions[conflict.source] = resolved
        return resolved

    def get_resolution(self, source: str) -> Optional[ConflictRecord]:
        return self._resolutions.get(source)

    def get_all_resolutions(self) -> Dict[str, ConflictRecord]:
        return dict(self._resolutions)

    def clear(self) -> None:
        self._resolutions.clear()


def build_candidates_from_sources(
    source: str,
    entity_type: EntityType,
    user_override: Optional[str] = None,
    runtime_translation: Optional[str] = None,
    learning_translation: Optional[str] = None,
    auto_translation: Optional[str] = None,
) -> List[ConflictCandidate]:
    """Build candidate list from various sources with proper priorities."""
    candidates = []

    if user_override:
        candidates.append(ConflictCandidate(
            translation=user_override,
            source=ResolutionSource.USER,
            confidence=1.0,
            metadata={"source": "user_override"},
        ))

    if runtime_translation:
        candidates.append(ConflictCandidate(
            translation=runtime_translation,
            source=ResolutionSource.RUNTIME,
            confidence=0.9,
            metadata={"source": "runtime"},
        ))

    if learning_translation:
        candidates.append(ConflictCandidate(
            translation=learning_translation,
            source=ResolutionSource.LEARNING,
            confidence=0.7,
            metadata={"source": "learning"},
        ))

    if auto_translation:
        candidates.append(ConflictCandidate(
            translation=auto_translation,
            source=ResolutionSource.AUTO,
            confidence=0.5,
            metadata={"source": "auto"},
        ))

    return candidates


__all__ = [
    "ConflictDetector",
    "ConflictResolver",
    "ConflictCandidate",
    "build_candidates_from_sources",
]