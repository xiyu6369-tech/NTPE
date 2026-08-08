"""RM-7.3 Entity Normalizer — Main normalization engine.

Integrates identity resolution, name form classification, and conflict resolution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    CanonicalEntity,
    ConflictRecord,
    ConflictSeverity,
    EntityType,
    EntityNameForms,
    NormalizationContext,
    NormalizationResult,
    NormalizedEntity,
)
from .identity import (
    EntityIdentityRegistry,
    build_canonical_entity,
    get_identity_registry,
    register_entity,
    resolve_entity,
)
from .name_form import (
    build_normalized_entity,
    classify_name_form,
    extract_context_from_text,
    resolve_name_form,
)
from .conflict import (
    ConflictDetector,
    ConflictResolver,
    ConflictCandidate,
    build_candidates_from_sources,
    ResolutionSource,
)


@dataclass
class EntityNormalizer:
    """Main entity normalization engine.

    Pipeline:
    1. Entity Identity Resolution (map source to CanonicalEntity)
    2. Name Form Classification (determine surface form type)
    3. Context-aware Translation Resolution (preserve address level)
    4. Conflict Detection & Resolution
    """

    registry: EntityIdentityRegistry = None
    detector: ConflictDetector = None
    resolver: ConflictResolver = None

    def __post_init__(self):
        if self.registry is None:
            self.registry = get_identity_registry()
        if self.detector is None:
            self.detector = ConflictDetector()
        if self.resolver is None:
            self.resolver = ConflictResolver()

    def normalize(
        self,
        text: str,
        known_entities: Optional[Dict[str, Dict[str, Any]]] = None,
        user_overrides: Optional[Dict[str, str]] = None,
    ) -> NormalizationResult:
        """Normalize all entities in a text chunk.

        Args:
            text: Korean source text
            known_entities: Dict of source_name -> {canonical_translation, entity_type, ...}
            user_overrides: Dict of source_name -> user_defined_translation

        Returns:
            NormalizationResult with normalized entities and conflicts
        """
        # Register known entities
        if known_entities:
            self._register_known_entities(known_entities)

        # Extract entities from text (simplified - in practice use entity_resolver.extractor)
        extracted = self._extract_entities(text)

        # Check conflicts BEFORE applying user overrides
        # Store original translations for conflict detection
        original_translations = {}
        for source_text, position, entity_type in extracted:
            entity = self.registry.resolve_source(source_text)
            if entity and entity.name_forms.full_name:
                original_translations[source_text] = entity.name_forms.full_name.translation

        # Detect conflicts
        conflicts = []
        if user_overrides:
            for source_text, user_translation in user_overrides.items():
                if source_text in original_translations:
                    runtime_translation = original_translations[source_text]
                    if user_translation != runtime_translation:
                        # Create conflict record
                        conflict = ConflictRecord(
                            source=source_text,
                            entity_type=entity_type,  # Need to get entity_type
                            candidates=[runtime_translation, user_translation],
                            severity=ConflictSeverity.HIGH,
                            resolution=user_translation,
                            resolution_source=ResolutionSource.USER,
                        )
                        conflicts.append(conflict)

        # Apply user overrides
        if user_overrides:
            self._apply_user_overrides(user_overrides)

        # Normalize each extracted entity
        result = NormalizationResult()
        for source_text, position, entity_type in extracted:
            entity = self.registry.resolve_source(source_text)
            if not entity:
                # Unknown entity - create minimal canonical entity
                entity = build_canonical_entity(
                    source_name=source_text,
                    canonical_translation=source_text,  # Keep as-is for unknown
                    entity_type=entity_type,
                )
                self.registry.register(entity)

            # Extract context
            context = extract_context_from_text(text, position)

            # Build normalized entity
            normalized = build_normalized_entity(source_text, entity, context)
            if normalized:
                result = result.add_entity(normalized)

        # Add detected conflicts
        for conflict in conflicts:
            result = result.add_conflict(conflict)

        return result

    def _register_known_entities(self, known_entities: Dict[str, Dict[str, Any]]) -> None:
        """Register known entities from knowledge runtime."""
        for source_name, info in known_entities.items():
            canonical = info.get("canonical_translation") or info.get("translation") or source_name
            entity_type_str = info.get("entity_type", "TERM")
            entity_type = EntityType(entity_type_str) if isinstance(entity_type_str, str) else entity_type_str

            entity = build_canonical_entity(
                source_name=source_name,
                canonical_translation=canonical,
                entity_type=entity_type,
                metadata=info.get("metadata", {}),
            )
            self.registry.register(entity)

    def _apply_user_overrides(self, user_overrides: Dict[str, str]) -> None:
        """Apply user overrides to existing entities."""
        for source_name, translation in user_overrides.items():
            entity = self.registry.resolve_source(source_name)
            if entity:
                # Update the entity's canonical translation and full_name form
                new_forms = entity.name_forms
                if new_forms.full_name:
                    # Create updated forms with new translation
                    updated_forms = EntityNameForms(
                        full_name=entity.name_forms.full_name.__class__(
                            source=entity.name_forms.full_name.source,
                            translation=translation,
                            form_type=entity.name_forms.full_name.form_type,
                        ),
                        given_name=entity.name_forms.given_name,
                        family_name=entity.name_forms.family_name,
                        nicknames=entity.name_forms.nicknames,
                        titles=entity.name_forms.titles,
                        formal=entity.name_forms.formal,
                        intimate=entity.name_forms.intimate,
                        relationship=entity.name_forms.relationship,
                        metadata=entity.name_forms.metadata,
                    )
                    self.registry.update_name_forms(entity.entity_id, updated_forms)

    def _extract_entities(self, text: str) -> List[Tuple[str, int, EntityType]]:
        """Extract entities from text.

        Returns list of (source_text, position, entity_type).
        This is a simplified version - in production use entity_resolver.extractor.
        """
        extracted = []

        # Find all registered entities in text
        for entity in self.registry.get_all_entities():
            for form in entity.name_forms.get_all_forms():
                source = form.source
                # Find all occurrences
                start = 0
                while True:
                    pos = text.find(source, start)
                    if pos == -1:
                        break
                    extracted.append((source, pos, entity.entity_type))
                    start = pos + 1

        # Sort by position
        extracted.sort(key=lambda x: x[1])

        # Deduplicate overlapping matches (keep longest)
        deduplicated = []
        for source, pos, etype in extracted:
            overlap = False
            for d_source, d_pos, d_etype in deduplicated:
                if pos >= d_pos and pos < d_pos + len(d_source):
                    overlap = True
                    break
            if not overlap:
                deduplicated.append((source, pos, etype))

        return deduplicated


def create_normalizer(
    registry: Optional[EntityIdentityRegistry] = None
) -> EntityNormalizer:
    """Factory function to create a normalizer."""
    return EntityNormalizer(registry=registry)


__all__ = [
    "EntityNormalizer",
    "create_normalizer",
]