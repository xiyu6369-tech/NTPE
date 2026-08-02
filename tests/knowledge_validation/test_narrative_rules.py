"""
Tests for Narrative Business Rules (NA-001 to NA-005)
RM-5.7.3B Business Rule Validation Engine
"""

import pytest

from core.knowledge_validation.rules.narrative_rules import (
    NARRATIVE_RULES,
    NarrativeAffectedCharactersUniqueRule,
    NarrativeEventTypeValidRule,
    NarrativeImpactLevelValidRule,
    NarrativeTimelineOrderingRule,
    NarrativeWorldRuleImmutableRule,
)
from core.knowledge_validation.rules.base import RuleContext
from core.knowledge_validation.validation_codes import BusinessRuleCode


class TestNarrativeEventTypeValidRule:
    """Tests for NA-001: event_type valid."""

    def setup_method(self):
        self.rule = NarrativeEventTypeValidRule()

    def test_valid_plot_point_type(self):
        entity = {
            "entity_type": "narrative",
            "attributes": {
                "narrative_type": "plot_point",
                "plot_point": {"type": "inciting"},
            },
        }
        context = RuleContext(entity=entity, entity_type="narrative")
        errors = self.rule.validate(context)
        assert len(errors) == 0

    def test_invalid_plot_point_type(self):
        entity = {
            "entity_type": "narrative",
            "attributes": {
                "narrative_type": "plot_point",
                "plot_point": {"type": "invalid"},
            },
        }
        context = RuleContext(entity=entity, entity_type="narrative")
        errors = self.rule.validate(context)
        assert len(errors) == 1
        assert errors[0].keyword == BusinessRuleCode.NA001.value


class TestNarrativeImpactLevelValidRule:
    """Tests for NA-002: impact_level valid."""

    def setup_method(self):
        self.rule = NarrativeImpactLevelValidRule()

    def test_valid_impact_level(self):
        for level in [1, 5, 10]:
            entity = {
                "entity_type": "narrative",
                "attributes": {
                    "narrative_type": "character_milestone",
                    "character_milestone": {"impact_level": level},
                },
            }
            context = RuleContext(entity=entity, entity_type="narrative")
            errors = self.rule.validate(context)
            assert len(errors) == 0

    def test_invalid_impact_level(self):
        entity = {
            "entity_type": "narrative",
            "attributes": {
                "narrative_type": "character_milestone",
                "character_milestone": {"impact_level": 11},
            },
        }
        context = RuleContext(entity=entity, entity_type="narrative")
        errors = self.rule.validate(context)
        assert len(errors) == 1
        assert errors[0].keyword == BusinessRuleCode.NA002.value


class TestNarrativeTimelineOrderingRule:
    """Tests for NA-003: timeline ordering valid."""

    def setup_method(self):
        self.rule = NarrativeTimelineOrderingRule()

    def test_valid_increasing_positions(self):
        entity = {
            "entity_type": "narrative",
            "attributes": {
                "narrative_type": "timeline",
                "timeline": {
                    "events": [
                        {"position": 1, "event_id": "e1"},
                        {"position": 2, "event_id": "e2"},
                        {"position": 3, "event_id": "e3"},
                    ]
                },
            },
        }
        context = RuleContext(entity=entity, entity_type="narrative")
        errors = self.rule.validate(context)
        assert len(errors) == 0

    def test_invalid_decreasing_positions(self):
        entity = {
            "entity_type": "narrative",
            "attributes": {
                "narrative_type": "timeline",
                "timeline": {
                    "events": [
                        {"position": 2, "event_id": "e1"},
                        {"position": 1, "event_id": "e2"},
                    ]
                },
            },
        }
        context = RuleContext(entity=entity, entity_type="narrative")
        errors = self.rule.validate(context)
        assert len(errors) == 1
        assert errors[0].keyword == BusinessRuleCode.NA003.value
class TestNarrativeAffectedCharactersUniqueRule:
    """Tests for NA-004: affected_characters unique."""

    def setup_method(self):
        self.rule = NarrativeAffectedCharactersUniqueRule()

    def test_valid_unique_characters(self):
        entity = {
            "entity_type": "narrative",
            "attributes": {
                "narrative_type": "plot_point",
                "plot_point": {"affected_characters": ["char1", "char2"]},
            },
        }
        context = RuleContext(entity=entity, entity_type="narrative")
        errors = self.rule.validate(context)
        assert len(errors) == 0

    def test_duplicate_characters(self):
        entity = {
            "entity_type": "narrative",
            "attributes": {
                "narrative_type": "plot_point",
                "plot_point": {"affected_characters": ["char1", "char1"]},
            },
        }
        context = RuleContext(entity=entity, entity_type="narrative")
        errors = self.rule.validate(context)
        assert len(errors) == 1
        assert errors[0].keyword == BusinessRuleCode.NA004.value


class TestNarrativeWorldRuleImmutableRule:
    """Tests for NA-005: world_rule immutable."""

    def setup_method(self):
        self.rule = NarrativeWorldRuleImmutableRule()

    def test_valid_rule_id(self):
        for rid in ["WR-1", "WR-123"]:
            entity = {
                "entity_type": "narrative",
                "attributes": {
                    "narrative_type": "world_rule",
                    "world_rule": {"rule_id": rid},
                },
            }
            context = RuleContext(entity=entity, entity_type="narrative")
            errors = self.rule.validate(context)
            assert len(errors) == 0

    def test_invalid_rule_id(self):
        entity = {
            "entity_type": "narrative",
            "attributes": {
                "narrative_type": "world_rule",
                "world_rule": {"rule_id": "WR-ABC"},
            },
        }
        context = RuleContext(entity=entity, entity_type="narrative")
        errors = self.rule.validate(context)
        assert len(errors) == 1
        assert errors[0].keyword == BusinessRuleCode.NA005.value


class TestNarrativeRulesIntegration:
    """Integration tests for all narrative rules."""

    def test_all_rules_pass_valid_entities(self):
        entities = [
            {
                "entity_type": "narrative",
                "attributes": {
                    "narrative_type": "plot_point",
                    "plot_point": {"type": "inciting", "affected_characters": ["c1"]},
                },
            },
            {
                "entity_type": "narrative",
                "attributes": {
                    "narrative_type": "character_milestone",
                    "character_milestone": {"milestone_type": "breakthrough", "impact_level": 5},
                },
            },
            {
                "entity_type": "narrative",
                "attributes": {
                    "narrative_type": "world_rule",
                    "world_rule": {"category": "magic_system", "rule_id": "WR-1"},
                },
            },
        ]
        all_errors = []
        for entity in entities:
            context = RuleContext(entity=entity, entity_type="narrative")
            for rule in NARRATIVE_RULES:
                errors = rule.validate(context)
                all_errors.extend(errors)
        assert len(all_errors) == 0