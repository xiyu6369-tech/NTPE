"""RM-7.2 Entity Resolver.

Resolves extracted entities using Knowledge Evolution priority:
USER > RUNTIME > LEARNING > AUTO

USER overrides always win and cannot be overridden by lower levels.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.knowledge_runtime.merger import MergedRuntime
from .models import (
    EntityInjectionSet,
    EntityType,
    ExtractedEntity,
    InjectionSource,
    ResolvedEntity,
    UNKNOWN_TRANSLATION,
)


class EntityResolver:
    """Resolve entities using Knowledge Evolution hierarchy."""

    def __init__(
        self,
        runtime: Optional[MergedRuntime] = None,
        user_overrides: Optional[Dict[str, str]] = None,
        learning_data: Optional[Dict[str, str]] = None,
    ):
        self.runtime = runtime
        self.user_overrides = user_overrides or {}
        self.learning_data = learning_data or {}

    def resolve(self, extracted: List[ExtractedEntity]) -> EntityInjectionSet:
        """Resolve all extracted entities.

        Resolution order:
        1. USER - User-defined overrides (highest priority, immutable)
        2. RUNTIME - Merged runtime knowledge (character, glossary, scene)
        3. LEARNING - Historical learning patterns
        4. AUTO - Unknown (no predefined translation)

        Args:
            extracted: List of ExtractedEntity from extractor

        Returns:
            EntityInjectionSet with resolved entities
        """
        resolved_entities = []

        for entity in extracted:
            resolved = self._resolve_single(entity)
            resolved_entities.append(resolved)

        return EntityInjectionSet(
            entities=resolved_entities,
            metadata={
                "total_extracted": len(extracted),
                "user_overrides": sum(1 for e in resolved_entities if e.source_level == InjectionSource.USER.value),
                "runtime_resolved": sum(1 for e in resolved_entities if e.source_level == InjectionSource.RUNTIME.value),
                "learning_resolved": sum(1 for e in resolved_entities if e.source_level == InjectionSource.LEARNING.value),
                "auto_unknown": sum(1 for e in resolved_entities if e.source_level == InjectionSource.AUTO.value),
            },
        )

    def _resolve_single(self, extracted: ExtractedEntity) -> ResolvedEntity:
        """Resolve a single entity through the hierarchy."""
        source = extracted.source

        # 1. USER OVERRIDE - Highest priority, immutable
        if source in self.user_overrides:
            return ResolvedEntity(
                source=source,
                target=self.user_overrides[source],
                entity_type=extracted.entity_type,
                source_level=InjectionSource.USER.value,
                metadata={"override": True, "context": extracted.context},
            )

        # 2. RUNTIME - Merged knowledge (character, glossary, scene)
        if self.runtime:
            runtime_target = self._resolve_from_runtime(source, extracted.entity_type)
            if runtime_target:
                return ResolvedEntity(
                    source=source,
                    target=runtime_target,
                    entity_type=extracted.entity_type,
                    source_level=InjectionSource.RUNTIME.value,
                    metadata={"context": extracted.context},
                )

        # 3. LEARNING - Historical patterns
        if source in self.learning_data:
            return ResolvedEntity(
                source=source,
                target=self.learning_data[source],
                entity_type=extracted.entity_type,
                source_level=InjectionSource.LEARNING.value,
                metadata={"context": extracted.context, "source": "learning"},
            )

        # 4. AUTO - Unknown (no predefined translation)
        return ResolvedEntity(
            source=source,
            target=UNKNOWN_TRANSLATION,
            entity_type=extracted.entity_type,
            source_level=InjectionSource.AUTO.value,
            metadata={"context": extracted.context, "unknown": True},
        )

    def _resolve_from_runtime(self, source: str, entity_type: str) -> Optional[str]:
        """Resolve entity from MergedRuntime domains.

        Checks domains in priority order based on entity_type.
        """
        if entity_type == EntityType.CHARACTER.value:
            domain = self.runtime.get_domain("character")
            if domain and source in domain.entries:
                return str(domain.entries[source])

        elif entity_type == EntityType.TERMINOLOGY.value:
            domain = self.runtime.get_domain("glossary")
            if domain and source in domain.entries:
                return str(domain.entries[source])

        elif entity_type == EntityType.PLACE.value:
            domain = self.runtime.get_domain("scene")
            if domain and source in domain.entries:
                return str(domain.entries[source])

        elif entity_type == EntityType.ORGANIZATION.value:
            # Try narrative domain for organizations
            domain = self.runtime.get_domain("narrative")
            if domain and source in domain.entries:
                return str(domain.entries[source])

        # Fallback: check all domains
        for domain_name in ["character", "glossary", "scene", "narrative", "style"]:
            domain = self.runtime.get_domain(domain_name)
            if domain and source in domain.entries:
                return str(domain.entries[source])

        return None

    def add_user_override(self, source: str, target: str) -> None:
        """Add a user override (immutable, highest priority)."""
        self.user_overrides[source] = target

    def remove_user_override(self, source: str) -> bool:
        """Remove a user override. Returns True if existed."""
        return self.user_overrides.pop(source, None) is not None

    def update_runtime(self, runtime: MergedRuntime) -> None:
        """Update the runtime reference."""
        self.runtime = runtime

    def update_learning(self, learning_data: Dict[str, str]) -> None:
        """Update learning data."""
        self.learning_data.update(learning_data)


def build_user_overrides_from_config(config: Dict[str, Any]) -> Dict[str, str]:
    """Build user overrides from configuration.

    Expected format:
    {
        "user_overrides": {
            "정태의": "鄭泰義",
            "일레이": "伊萊",
        }
    }
    """
    overrides = {}
    user_section = config.get("user_overrides") or config.get("entity_overrides")
    if isinstance(user_section, dict):
        for k, v in user_section.items():
            if isinstance(k, str) and isinstance(v, str):
                overrides[k] = v
    return overrides


def build_learning_data_from_history(history: List[Dict[str, Any]]) -> Dict[str, str]:
    """Build learning data from translation history.

    Expected history items:
    {"source": "정태의", "target": "鄭泰義", "confidence": 0.9}
    """
    learning = {}
    for item in history:
        source = item.get("source")
        target = item.get("target")
        confidence = item.get("confidence", 0.0)
        if source and target and confidence >= 0.8:  # High confidence threshold
            learning[source] = target
    return learning


__all__ = [
    "EntityResolver",
    "build_user_overrides_from_config",
    "build_learning_data_from_history",
]