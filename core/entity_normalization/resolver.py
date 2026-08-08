"""RM-7.3 Entity Normalization Resolver — Integration with existing Entity Resolver.

Bridges RM-7.2 EntityResolver with RM-7.3 EntityNormalization.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.entity_resolver.models import (
    EntityInjectionSet,
    EntityType as ResolverEntityType,
    ExtractedEntity,
    InjectionSource,
    ResolvedEntity,
)
from core.entity_resolver.resolver import EntityResolver as LegacyEntityResolver

from .models import (
    CanonicalEntity,
    EntityType,
    NormalizationContext,
    NormalizationResult,
    NormalizedEntity,
)
from .identity import (
    EntityIdentityRegistry,
    build_canonical_entity,
    map_ke_entity_type,
    map_resolver_entity_type,
    register_entity,
    resolve_entity,
)
from .name_form import (
    build_normalized_entity,
    extract_context_from_text,
)
from .normalizer import EntityNormalizer


class NormalizationResolver:
    """Resolver that combines RM-7.2 entity resolution with RM-7.3 normalization.

    Uses legacy EntityResolver for extraction and priority resolution,
    then applies normalization for surface form preservation.
    """

    def __init__(
        self,
        legacy_resolver: Optional[LegacyEntityResolver] = None,
        normalizer: Optional[EntityNormalizer] = None,
    ):
        self.legacy_resolver = legacy_resolver
        self.normalizer = normalizer or EntityNormalizer()

    def resolve_and_normalize(
        self,
        extracted: List[ExtractedEntity],
        text: str = "",
    ) -> NormalizationResult:
        """Resolve entities using legacy resolver, then normalize with form preservation."""
        # Step 1: Legacy resolution (USER > RUNTIME > LEARNING > AUTO)
        if self.legacy_resolver:
            injection_set = self.legacy_resolver.resolve(extracted)
        else:
            injection_set = EntityInjectionSet(entities=[])

        # Step 2: Build canonical entities from resolved entities
        self._build_canonical_entities(injection_set)

        # Step 3: Normalize with form preservation
        result = NormalizationResult()

        for extracted_entity in extracted:
            canonical = resolve_entity(extracted_entity.source)
            if not canonical:
                # Create minimal canonical for unknown
                entity_type = map_resolver_entity_type(extracted_entity.entity_type)

                canonical = build_canonical_entity(
                    source_name=extracted_entity.source,
                    canonical_translation=extracted_entity.source,  # Keep original for unknown
                    entity_type=entity_type,
                )
                register_entity(canonical)

            # Extract context from text
            context = NormalizationContext(
                source_text=extracted_entity.source,
                position=extracted_entity.position,
                surrounding_text=extracted_entity.context,
            )
            if text and extracted_entity.position >= 0:
                context = extract_context_from_text(text, extracted_entity.position)

            # Normalize
            normalized = build_normalized_entity(
                extracted_entity.source,
                canonical,
                context
            )
            if normalized:
                result = result.add_entity(normalized)

        return result

    def _build_canonical_entities(self, injection_set: EntityInjectionSet) -> None:
        """Build CanonicalEntities from ResolvedEntities.

        Implements surface-form linking: when a resolved source like '태의'
        or '태의야' is encountered, it is merged as a surface form of an
        existing entity '정태의' if it matches known name form patterns.
        Priority: USER > RUNTIME > LEARNING > AUTO.
        """
        from .identity import get_identity_registry

        for resolved in injection_set.entities:
            entity_type = map_resolver_entity_type(resolved.entity_type)

            # Check if we already have this entity (direct lookup)
            existing = resolve_entity(resolved.source)
            if existing:
                # The source is already a known form of an existing entity.
                # If the resolved source equals the entity's source_name AND
                # the new target is from USER, update the full_name translation.
                if (resolved.source == existing.source_name
                        and resolved.source_level == InjectionSource.USER.value
                        and existing.name_forms.full_name
                        and existing.name_forms.full_name.translation != resolved.target):
                    self._update_full_name_translation(existing, resolved.target)
                # Otherwise: source is a surface form, translation is already
                # stored in the appropriate form slot. No update needed.
                continue

            # Try to link as surface form of existing entity
            linked_entity = self._try_link_surface_form(resolved, entity_type)
            if linked_entity:
                continue

            # Create new canonical entity
            canonical = build_canonical_entity(
                source_name=resolved.source,
                canonical_translation=resolved.target,
                entity_type=entity_type,
                metadata={
                    "source_level": resolved.source_level,
                    "resolver_metadata": resolved.metadata,
                },
            )
            register_entity(canonical)

    def _try_link_surface_form(
        self,
        resolved,
        entity_type: EntityType,
    ) -> Optional[CanonicalEntity]:
        """Try to link a resolved entity as a surface form of an existing entity.

        Returns the linked entity if successful, None otherwise.

        Linking rules (in priority order):
        1. If source ends with given_name of an existing entity with INTIMATE
           suffix → set as intimate form
        2. If source equals given_name of an existing entity → already linked
           via name_forms registration
        3. If source starts with family_name + ' 씨' of an existing entity →
           set as formal form
        4. If source is a suffix-stripped form of an existing entity's full_name
        """
        from .identity import get_identity_registry
        from .models import NameFormTranslation, NameFormType

        registry = get_identity_registry()
        source = resolved.source
        target = resolved.target

        # Check all existing entities for potential linking
        for entity in registry.get_all_entities():
            if entity.entity_type != entity_type:
                continue

            forms = entity.name_forms
            full = forms.full_name
            if not full:
                continue

            # Rule 1: Intimate suffix on given_name
            if forms.given_name:
                for suffix in ["야", "아", "이", "군", "양"]:
                    if source == forms.given_name.source + suffix:
                        return self._add_form_to_entity(
                            entity,
                            NameFormTranslation(
                                source=source,
                                translation=target,
                                form_type=NameFormType.INTIMATE,
                            ),
                            resolved,
                        )

            # Rule 2: Formal suffix (family_name + " 씨")
            if forms.family_name:
                for suffix in ["씨", "님"]:
                    if source == forms.family_name.source + " " + suffix or source == forms.family_name.source + suffix:
                        return self._add_form_to_entity(
                            entity,
                            NameFormTranslation(
                                source=source,
                                translation=target,
                                form_type=NameFormType.FORMAL,
                            ),
                            resolved,
                        )

            # Rule 3: Full name with formal suffix
            if source.startswith(full.source + " ") or source == full.source + " 씨":
                return self._add_form_to_entity(
                    entity,
                    NameFormTranslation(
                        source=source,
                        translation=target,
                        form_type=NameFormType.FORMAL,
                    ),
                    resolved,
                )

            # Rule 4: Source is a suffix of full_name (potential given_name only)
            if full.source.endswith(source) and len(source) >= 2:
                # Source could be given_name - add as given_name form
                # Only if no given_name is already set, or this is a USER override
                if not forms.given_name or resolved.source_level == "USER":
                    # Compute translation: take last len(source) chars of translation
                    if full.translation.endswith(target) and len(target) >= 2:
                        return self._add_form_to_entity(
                            entity,
                            NameFormTranslation(
                                source=source,
                                translation=target,
                                form_type=NameFormType.GIVEN_NAME,
                            ),
                            resolved,
                        )

        return None

    def _add_form_to_entity(
        self,
        entity: CanonicalEntity,
        new_form: "NameFormTranslation",
        resolved,
    ) -> CanonicalEntity:
        """Add a new name form to an existing entity, replacing the matching field."""
        from .identity import get_identity_registry
        from .models import NameFormType

        registry = get_identity_registry()
        forms = entity.name_forms

        # Build updated forms based on the new form's type
        if new_form.form_type == NameFormType.INTIMATE:
            updated_forms = forms.__class__(
                full_name=forms.full_name,
                given_name=forms.given_name,
                family_name=forms.family_name,
                nicknames=forms.nicknames,
                titles=forms.titles,
                formal=forms.formal,
                intimate=new_form,
                relationship=forms.relationship,
                metadata=forms.metadata,
            )
        elif new_form.form_type == NameFormType.FORMAL:
            updated_forms = forms.__class__(
                full_name=forms.full_name,
                given_name=forms.given_name,
                family_name=forms.family_name,
                nicknames=forms.nicknames,
                titles=forms.titles,
                formal=new_form,
                intimate=forms.intimate,
                relationship=forms.relationship,
                metadata=forms.metadata,
            )
        elif new_form.form_type == NameFormType.GIVEN_NAME:
            updated_forms = forms.__class__(
                full_name=forms.full_name,
                given_name=new_form,
                family_name=forms.family_name,
                nicknames=forms.nicknames,
                titles=forms.titles,
                formal=forms.formal,
                intimate=forms.intimate,
                relationship=forms.relationship,
                metadata=forms.metadata,
            )
        else:
            return entity  # No update

        registry.update_name_forms(entity.entity_id, updated_forms)
        return registry.get_by_id(entity.entity_id)

    def _update_full_name_translation(self, entity: CanonicalEntity, new_translation: str) -> None:
        """Update entity's full_name translation (user override on primary source)."""
        from .identity import get_identity_registry
        registry = get_identity_registry()

        new_forms = entity.name_forms
        if new_forms.full_name:
            updated_forms = new_forms.__class__(
                full_name=new_forms.full_name.__class__(
                    source=new_forms.full_name.source,
                    translation=new_translation,
                    form_type=new_forms.full_name.form_type,
                ),
                given_name=new_forms.given_name,
                family_name=new_forms.family_name,
                nicknames=new_forms.nicknames,
                titles=new_forms.titles,
                formal=new_forms.formal,
                intimate=new_forms.intimate,
                relationship=new_forms.relationship,
                metadata=new_forms.metadata,
            )
            registry.update_name_forms(entity.entity_id, updated_forms)


def create_normalization_resolver(
    legacy_resolver: Optional[LegacyEntityResolver] = None,
) -> NormalizationResolver:
    """Factory to create a NormalizationResolver."""
    return NormalizationResolver(legacy_resolver=legacy_resolver)


__all__ = [
    "NormalizationResolver",
    "create_normalization_resolver",
]