"""Tests for entity_normalization normalizer module."""

import pytest

from core.entity_normalization.normalizer import (
    EntityNormalizer,
    create_normalizer,
)
from core.entity_normalization.models import (
    EntityType,
    NormalizationResult,
)


class TestEntityNormalizer:
    def test_normalize_known_entity(self):
        normalizer = create_normalizer()
        known = {
            "정태의": {
                "canonical_translation": "鄭泰義",
                "entity_type": "CHARACTER",
            }
        }
        result = normalizer.normalize("정태의가 말했다.", known_entities=known)
        assert len(result.entities) == 1
        assert result.entities[0].translation == "鄭泰義"
        assert result.entities[0].entity_type == EntityType.CHARACTER

    def test_normalize_with_user_override(self):
        normalizer = create_normalizer()
        known = {
            "정태의": {
                "canonical_translation": "鄭太義",
                "entity_type": "CHARACTER",
            }
        }
        overrides = {
            "정태의": "鄭泰義",  # User prefers different translation
        }
        result = normalizer.normalize("정태의가 말했다.", known_entities=known, user_overrides=overrides)
        assert len(result.entities) == 1
        # User override should win
        assert result.entities[0].translation == "鄭泰義"

    def test_normalize_multiple_entities(self):
        normalizer = create_normalizer()
        known = {
            "정태의": {"canonical_translation": "鄭泰義", "entity_type": "CHARACTER"},
            "서울": {"canonical_translation": "首爾", "entity_type": "LOCATION"},
        }
        result = normalizer.normalize("정태의가 서울에 갔다.", known_entities=known)
        assert len(result.entities) == 2

    def test_normalize_detects_conflict(self):
        normalizer = create_normalizer()
        known = {
            "정태의": {"canonical_translation": "鄭太義", "entity_type": "CHARACTER"},
        }
        overrides = {
            "정태의": "鄭泰義",
        }
        result = normalizer.normalize("정태의", known_entities=known, user_overrides=overrides)
        # Should have conflict detected
        assert len(result.conflicts) >= 1
        conflict = result.conflicts[0]
        assert conflict.resolution == "鄭泰義"  # User wins
        assert conflict.resolution_source.value == "USER"

    def test_normalize_unknown_entity(self):
        normalizer = create_normalizer()
        # Unknown entities are not extracted unless in known_entities
        result = normalizer.normalize("미지수")
        # No known entities = no extracted entities
        assert len(result.entities) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])