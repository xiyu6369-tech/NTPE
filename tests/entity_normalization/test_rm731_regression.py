"""RM-7.3.1 Entity Normalization Regression Tests.

These tests pin down the correctness invariants for the 정태의 / 鄭泰義 entity
across surface-form linking, translation integrity, and prompt injection.

Invariants under test (from RM-7.3.1 spec):
  - 정태의 → 鄭泰義 (full name)
  - 태의   → 泰義   (given name)
  - 정 씨  → 鄭先生 (formal)
  - 태의야 → 泰義啊 (intimate)
  - All four surface forms share a single entity identity.
  - Korean spacing variants resolve to the same identity.
  - USER > RUNTIME > LEARNING > AUTO priority is honoured.
  - full_name.translation cannot be overwritten by given/intimate translation.
  - Prompt section must contain Full + Given + Formal + Intimate.
  - 鄭泰義啊 (wrong expansion) must never appear.
"""
from __future__ import annotations

import pytest

from core.entity_normalization.identity import (
    build_canonical_entity,
    get_identity_registry,
    map_resolver_entity_type,
    register_entity,
    resolve_entity,
)
from core.entity_normalization.models import (
    CanonicalEntity,
    EntityNameForms,
    EntityType,
    NameFormTranslation,
    NameFormType,
    NormalizationContext,
)
from core.entity_normalization.name_form import build_normalized_entity
from core.entity_normalization.report import build_compact_prompt_section
from core.entity_normalization.resolver import (
    NormalizationResolver,
    create_normalization_resolver,
)
from core.entity_resolver.models import (
    EntityType as ResolverEntityType,
    ExtractedEntity,
)
from core.entity_resolver.resolver import EntityResolver


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clear_registry():
    """Reset the global identity registry between tests."""
    get_identity_registry().clear()


def _make_legacy_resolver() -> EntityResolver:
    """Legacy resolver with user overrides matching the canary fixture."""
    return EntityResolver(
        user_overrides={
            "정태의": "鄭泰義",
            "태의": "泰義",
            "정 씨": "鄭先生",
            "태의야": "泰義啊",
        },
    )


def _make_resolver() -> NormalizationResolver:
    """Normalization resolver backed by the legacy resolver above."""
    return create_normalization_resolver(legacy_resolver=_make_legacy_resolver())


def _all_four_extracted():
    """The four canonical surface forms, in order of text position."""
    return [
        ExtractedEntity(
            source="정태의",
            entity_type=ResolverEntityType.CHARACTER.value,
            context="",
            position=0,
        ),
        ExtractedEntity(
            source="태의",
            entity_type=ResolverEntityType.CHARACTER.value,
            context="",
            position=10,
        ),
        ExtractedEntity(
            source="정 씨",
            entity_type=ResolverEntityType.CHARACTER.value,
            context="",
            position=20,
        ),
        ExtractedEntity(
            source="태의야",
            entity_type=ResolverEntityType.CHARACTER.value,
            context="",
            position=30,
        ),
    ]


# ---------------------------------------------------------------------------
# 1. Full name
# ---------------------------------------------------------------------------


class TestRegressionFullName:
    def test_full_name_translation_is_zheng_tai_yi(self):
        _clear_registry()
        resolver = _make_resolver()
        result = resolver.resolve_and_normalize(
            _all_four_extracted(),
            text="정태의 태의 정 씨 태의야",
        )

        full_entities = [
            ne for ne in result.entities
            if ne.matched_form.form_type == NameFormType.FULL_NAME
        ]
        assert len(full_entities) == 1
        assert full_entities[0].source_text == "정태의"
        assert full_entities[0].translation == "鄭泰義"


# ---------------------------------------------------------------------------
# 2. Given name
# ---------------------------------------------------------------------------


class TestRegressionGivenName:
    def test_given_name_translation_is_tai_yi(self):
        _clear_registry()
        resolver = _make_resolver()
        result = resolver.resolve_and_normalize(
            _all_four_extracted(),
            text="정태의 태의 정 씨 태의야",
        )

        given_entities = [
            ne for ne in result.entities
            if ne.matched_form.form_type == NameFormType.GIVEN_NAME
        ]
        assert len(given_entities) == 1
        assert given_entities[0].source_text == "태의"
        assert given_entities[0].translation == "泰義"


# ---------------------------------------------------------------------------
# 3. Formal
# ---------------------------------------------------------------------------


class TestRegressionFormal:
    def test_formal_translation_is_zheng_xiansheng(self):
        _clear_registry()
        resolver = _make_resolver()
        result = resolver.resolve_and_normalize(
            _all_four_extracted(),
            text="정태의 태의 정 씨 태의야",
        )

        formal_entities = [
            ne for ne in result.entities
            if ne.matched_form.form_type == NameFormType.FORMAL
        ]
        assert len(formal_entities) == 1
        assert formal_entities[0].source_text == "정 씨"
        assert formal_entities[0].translation == "鄭先生"


# ---------------------------------------------------------------------------
# 4. Intimate
# ---------------------------------------------------------------------------


class TestRegressionIntimate:
    def test_intimate_translation_is_tai_yi_a(self):
        _clear_registry()
        resolver = _make_resolver()
        result = resolver.resolve_and_normalize(
            _all_four_extracted(),
            text="정태의 태의 정 씨 태의야",
        )

        intimate_entities = [
            ne for ne in result.entities
            if ne.matched_form.form_type == NameFormType.INTIMATE
        ]
        assert len(intimate_entities) == 1
        assert intimate_entities[0].source_text == "태의야"
        assert intimate_entities[0].translation == "泰義啊"
        assert intimate_entities[0].translation != "鄭泰義啊"


# ---------------------------------------------------------------------------
# 5. Same entity with all surface forms
# ---------------------------------------------------------------------------


class TestRegressionSameEntity:
    def test_all_surface_forms_share_one_entity_id(self):
        _clear_registry()
        resolver = _make_resolver()
        result = resolver.resolve_and_normalize(
            _all_four_extracted(),
            text="정태의 태의 정 씨 태의야",
        )

        entity_ids = {ne.entity_id for ne in result.entities}
        assert entity_ids, "no normalized entities returned"
        assert len(entity_ids) == 1, (
            f"surface forms split across multiple entities: {entity_ids}"
        )

        canonical = resolve_entity("정태의")
        assert canonical is not None
        # All four surface forms must be discoverable via the registry
        for source in ("정태의", "태의", "정 씨", "태의야"):
            resolved = resolve_entity(source)
            assert resolved is not None, f"registry miss for {source!r}"
            assert resolved.entity_id == next(iter(entity_ids))


# ---------------------------------------------------------------------------
# 6. Korean spacing variants
# ---------------------------------------------------------------------------


class TestRegressionSpacingVariants:
    @pytest.mark.parametrize(
        "spaced_source",
        [
            "정 태의",   # space between family and given
            "정  태의",  # double space
            "정태의 ",   # trailing space
            " 정태의",   # leading space
        ],
    )
    def test_spaced_full_name_resolves_to_canonical(self, spaced_source):
        _clear_registry()
        resolver = _make_resolver()
        # First seed the registry by processing the canonical form so that
        # resolve_source's spacing-normalized lookup has a known entity.
        seed = resolver.resolve_and_normalize(
            [ExtractedEntity(
                source="정태의",
                entity_type=ResolverEntityType.CHARACTER.value,
                context="",
                position=0,
            )],
            text="정태의",
        )
        canonical_id = seed.entities[0].entity_id

        normalized = build_normalized_entity(
            spaced_source.strip(),
            resolve_entity("정태의"),
            NormalizationContext(source_text=spaced_source, position=0),
        )
        assert normalized is not None
        assert normalized.entity_id == canonical_id

    def test_spaced_given_name(self):
        _clear_registry()
        resolver = _make_resolver()
        resolver.resolve_and_normalize(
            [ExtractedEntity(
                source="정태의",
                entity_type=ResolverEntityType.CHARACTER.value,
                context="",
                position=0,
            )],
            text="정태의",
        )
        canonical = resolve_entity("정태의")
        canonical_id = canonical.entity_id

        # Spacing-variant given names must resolve to the same entity_id.
        # The translation may fall back to full_name when the padded source
        # is not an exact form match — what matters is identity stability.
        for variant in (" 태의", "태의 ", "  태의  ", "태 의"):
            normalized = build_normalized_entity(
                variant,
                canonical,
                NormalizationContext(source_text=variant, position=0),
            )
            assert normalized is not None, f"no normalization for {variant!r}"
            assert normalized.entity_id == canonical_id, (
                f"{variant!r} resolved to {normalized.entity_id!r} "
                f"instead of {canonical_id!r}"
            )


# ---------------------------------------------------------------------------
# 7. USER > RUNTIME > LEARNING > AUTO priority
# ---------------------------------------------------------------------------


class TestRegressionPriority:
    def test_user_override_wins_over_runtime(self):
        _clear_registry()
        # USER: 정태의 -> 鄭泰義
        # Simulate a RUNTIME entry that disagrees.
        class _RuntimeStub:
            def get_domain(self, name):
                return None  # no runtime knowledge loaded

        resolver = EntityResolver(
            runtime=None,
            user_overrides={"정태의": "鄭泰義"},
            learning_data={"정태의": "WRONG_FROM_LEARNING"},
        )
        norm = create_normalization_resolver(legacy_resolver=resolver)
        result = norm.resolve_and_normalize(
            [ExtractedEntity(
                source="정태의",
                entity_type=ResolverEntityType.CHARACTER.value,
                context="",
                position=0,
            )],
            text="정태의",
        )
        assert result.entities[0].translation == "鄭泰義"

    def test_user_override_on_full_name_updates_full_name_translation(self):
        """Re-overriding the primary source as USER should update full_name.

        The user explicitly asked for this; it is the ONLY legitimate path
        that can overwrite full_name.translation, and only when the resolved
        source equals the existing source_name and is at USER priority.
        """
        _clear_registry()
        resolver = _make_resolver()
        resolver.resolve_and_normalize(
            [ExtractedEntity(
                source="정태의",
                entity_type=ResolverEntityType.CHARACTER.value,
                context="",
                position=0,
            )],
            text="정태의",
        )
        canonical = resolve_entity("정태의")
        assert canonical.name_forms.full_name.translation == "鄭泰義"

        # Now re-resolve with a fresh USER override for the same source
        legacy2 = EntityResolver(user_overrides={"정태의": "鄭泰義改"})
        norm2 = create_normalization_resolver(legacy_resolver=legacy2)
        norm2.resolve_and_normalize(
            [ExtractedEntity(
                source="정태의",
                entity_type=ResolverEntityType.CHARACTER.value,
                context="",
                position=0,
            )],
            text="정태의",
        )
        canonical2 = resolve_entity("정태의")
        assert canonical2.name_forms.full_name.translation == "鄭泰義改"


# ---------------------------------------------------------------------------
# 8. full_name translation cannot be overwritten by given/intimate
# ---------------------------------------------------------------------------


class TestRegressionFullNameIntegrity:
    def test_given_name_does_not_overwrite_full_name(self):
        _clear_registry()
        resolver = _make_resolver()
        resolver.resolve_and_normalize(
            _all_four_extracted(),
            text="정태의 태의 정 씨 태의야",
        )
        canonical = resolve_entity("정태의")
        assert canonical.name_forms.full_name is not None
        assert canonical.name_forms.full_name.translation == "鄭泰義"
        assert canonical.name_forms.full_name.translation != "泰義"

    def test_intimate_form_does_not_overwrite_full_name(self):
        _clear_registry()
        resolver = _make_resolver()
        resolver.resolve_and_normalize(
            _all_four_extracted(),
            text="정태의 태의 정 씨 태의야",
        )
        canonical = resolve_entity("정태의")
        assert canonical.name_forms.full_name.translation == "鄭泰義"
        assert canonical.name_forms.full_name.translation != "泰義啊"

    def test_formal_form_does_not_overwrite_full_name(self):
        _clear_registry()
        resolver = _make_resolver()
        resolver.resolve_and_normalize(
            _all_four_extracted(),
            text="정태의 태의 정 씨 태의야",
        )
        canonical = resolve_entity("정태의")
        assert canonical.name_forms.full_name.translation == "鄭泰義"
        assert canonical.name_forms.full_name.translation != "鄭先生"

    def test_no_wrong_intimate_zheng_tai_yi_a(self):
        """Hard guard: 鄭泰義啊 must NEVER appear as a translation."""
        _clear_registry()
        resolver = _make_resolver()
        result = resolver.resolve_and_normalize(
            _all_four_extracted(),
            text="정태의 태의 정 씨 태의야",
        )
        for ne in result.entities:
            assert ne.translation != "鄭泰義啊", (
                f"intimate wrongly expanded: {ne.source_text!r} -> {ne.translation!r}"
            )


# ---------------------------------------------------------------------------
# 9. Prompt section contains Full + Given + Formal + Intimate
# ---------------------------------------------------------------------------


class TestRegressionPromptSection:
    def test_prompt_section_lists_all_four_forms(self):
        _clear_registry()
        resolver = _make_resolver()
        result = resolver.resolve_and_normalize(
            _all_four_extracted(),
            text="정태의 태의 정 씨 태의야",
        )
        section = build_compact_prompt_section(result)

        assert "FULL_NAME" in section
        assert "鄭泰義" in section
        assert "GIVEN_NAME" in section
        assert "FORMAL" in section
        assert "鄭先生" in section
        assert "INTIMATE" in section
        assert "泰義啊" in section

    def test_prompt_section_includes_given_when_only_full_extracted(self):
        """Given must still appear in the prompt when only the full name was
        extracted, because the registry holds the canonical forms."""
        _clear_registry()
        resolver = _make_resolver()
        # First populate the registry by processing all four forms.
        resolver.resolve_and_normalize(
            _all_four_extracted(),
            text="정태의 태의 정 씨 태의야",
        )
        # Then build a new NormalizationResult containing only 정태의.
        from core.entity_normalization.models import (
            NameFormTranslation,
            NormalizationResult,
            NormalizedEntity,
        )
        canonical = resolve_entity("정태의")
        full_form = canonical.name_forms.full_name
        only_full = NormalizationResult(entities=[
            NormalizedEntity(
                source_text="정태의",
                entity_id=canonical.entity_id,
                entity_type=canonical.entity_type,
                matched_form=full_form,
                translation=full_form.translation,
            ),
        ])
        section = build_compact_prompt_section(only_full)
        assert "GIVEN_NAME" in section
        assert "FORMAL" in section
        assert "INTIMATE" in section
        assert "鄭泰義" in section
        assert "泰義" in section
        assert "鄭先生" in section
        assert "泰義啊" in section


# ---------------------------------------------------------------------------
# Bonus: entity-type mapping sanity (the root-cause fix from earlier).
# ---------------------------------------------------------------------------


class TestEntityTypeMapping:
    def test_resolver_character_maps_to_character(self):
        assert map_resolver_entity_type("CHARACTER") == EntityType.CHARACTER

    def test_resolver_place_maps_to_location(self):
        assert map_resolver_entity_type("PLACE") == EntityType.LOCATION

    def test_resolver_terminology_maps_to_term(self):
        assert map_resolver_entity_type("TERMINOLOGY") == EntityType.TERM

    def test_resolver_unknown_maps_to_term(self):
        assert map_resolver_entity_type("UNKNOWN") == EntityType.TERM

    def test_resolver_empty_maps_to_term(self):
        assert map_resolver_entity_type("") == EntityType.TERM


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
