"""Tests for Entity Extractor (RM-7.2)."""

import pytest

from core.entity_resolver import (
    EntityExtractor,
    ExtractedEntity,
    EntityType,
    build_known_entities_from_runtime,
)
from core.knowledge_runtime.merger import MergedRuntime, MergedKnowledge


class MockRuntime:
    """Mock MergedRuntime for testing."""

    def __init__(self, domains: dict):
        self.domains = {}
        for name, entries in domains.items():
            self.domains[name] = MergedKnowledge(
                domain=name,
                entries=entries,
                strategy="key_override",
            )

    def get_domain(self, domain: str):
        return self.domains.get(domain)


def test_extractor_basic_extraction():
    """Test basic entity extraction from chunk."""
    known = {
        "정태의": EntityType.CHARACTER.value,
        "일레이": EntityType.CHARACTER.value,
        "신림동": EntityType.PLACE.value,
    }
    extractor = EntityExtractor(known_entities=known)

    chunk = "정태의가 일레이를 만나러 신림동에 갔다."
    extracted = extractor.extract(chunk)

    assert len(extracted) == 3
    assert extracted[0].source == "정태의"
    assert extracted[0].entity_type == EntityType.CHARACTER.value
    assert extracted[1].source == "일레이"
    assert extracted[2].source == "신림동"
    assert extracted[2].entity_type == EntityType.PLACE.value


def test_extractor_preserves_order():
    """Test that extracted entities maintain text order."""
    known = {
        "강민수": EntityType.CHARACTER.value,
        "유리": EntityType.CHARACTER.value,
        "홍콩": EntityType.PLACE.value,
    }
    extractor = EntityExtractor(known_entities=known)

    chunk = "강민수가 유리를 찾아 홍콩으로 갔다."
    extracted = extractor.extract(chunk)

    assert extracted[0].source == "강민수"
    assert extracted[1].source == "유리"
    assert extracted[2].source == "홍콩"
    assert extracted[0].position < extracted[1].position < extracted[2].position


def test_extractor_longest_match_first():
    """Test that longer entity names are matched first."""
    known = {
        "정태": EntityType.CHARACTER.value,
        "정태의": EntityType.CHARACTER.value,
    }
    extractor = EntityExtractor(known_entities=known)

    chunk = "정태의가 왔다."
    extracted = extractor.extract(chunk)

    # Should match "정태의" not "정태"
    assert len(extracted) == 1
    assert extracted[0].source == "정태의"


def test_extractor_no_duplicates():
    """Test that duplicate entities in chunk are not duplicated."""
    known = {
        "정태의": EntityType.CHARACTER.value,
    }
    extractor = EntityExtractor(known_entities=known)

    chunk = "정태의가 정태의를 불렀다. 정태의가 대답했다."
    extracted = extractor.extract(chunk)

    # Should only appear once
    assert len(extracted) == 1
    assert extracted[0].source == "정태의"


def test_extractor_empty_chunk():
    """Test extraction from empty chunk."""
    extractor = EntityExtractor(known_entities={"정태의": EntityType.CHARACTER.value})
    extracted = extractor.extract("")
    assert extracted == []


def test_extractor_no_known_entities():
    """Test extraction when no known entities in chunk."""
    known = {"정태의": EntityType.CHARACTER.value}
    extractor = EntityExtractor(known_entities=known)

    chunk = "아무도 모르는 사람이다."
    extracted = extractor.extract(chunk)
    assert extracted == []


def test_extractor_context_capture():
    """Test that context around entity is captured."""
    known = {"정태의": EntityType.CHARACTER.value}
    extractor = EntityExtractor(known_entities=known)

    chunk = "어제 정태의가 왔다."
    extracted = extractor.extract(chunk)

    assert len(extracted) == 1
    assert "정태의" in extracted[0].context
    assert "어제" in extracted[0].context or "왔다" in extracted[0].context


def test_build_known_entities_from_runtime():
    """Test building known entities dict from MergedRuntime."""
    runtime = MockRuntime({
        "character": {"정태의": "鄭泰義", "일레이": "伊萊"},
        "glossary": {"신림동 사건": "Sillim-dong Incident"},
        "scene": {"신림동": "Sillim-dong"},
    })

    known = build_known_entities_from_runtime(runtime)

    assert known["정태의"] == EntityType.CHARACTER.value
    assert known["일레이"] == EntityType.CHARACTER.value
    assert known["신림동 사건"] == EntityType.TERMINOLOGY.value
    assert known["신림동"] == EntityType.PLACE.value


def test_extractor_update_known_entities():
    """Test updating known entities after initialization."""
    extractor = EntityExtractor(known_entities={"정태의": EntityType.CHARACTER.value})

    chunk = "정태의와 일레이가 만났다."
    extracted = extractor.extract(chunk)
    assert len(extracted) == 1  # Only 정태의 known

    # Add new entity
    extractor.update_known_entities({"일레이": EntityType.CHARACTER.value})
    extracted = extractor.extract(chunk)
    assert len(extracted) == 2


def test_extractor_clear():
    """Test clearing known entities."""
    extractor = EntityExtractor(known_entities={"정태의": EntityType.CHARACTER.value})
    extractor.clear()

    chunk = "정태의가 왔다."
    extracted = extractor.extract(chunk)
    assert extracted == []


def test_extractor_custom_patterns():
    """Test extraction with custom regex patterns."""
    import re

    # Pattern for organization-like names
    org_pattern = re.compile(r"[가-힣]{2,}(?:회사|기관|조직|단체)")

    extractor = EntityExtractor(
        known_entities={},
        custom_patterns=[org_pattern],
    )

    chunk = "삼성전자회사가 발표했다."
    extracted = extractor.extract(chunk)

    # Should find via pattern
    assert len(extracted) >= 1
    found = any("회사" in e.source for e in extracted)
    assert found


if __name__ == "__main__":
    pytest.main([__file__, "-v"])