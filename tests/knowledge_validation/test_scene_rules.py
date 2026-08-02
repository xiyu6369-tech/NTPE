"""
Tests for Scene Business Rules (SC-001 to SC-005)
RM-5.7.3B Business Rule Validation Engine
"""

import pytest

from core.knowledge_validation.rules.scene_rules import (
    SCENE_RULES,
    SceneBoundaryTypeValidRule,
    SceneParticipantsUniqueRule,
    ScenePlotPointsUniqueRule,
    SceneSceneIdImmutableRule,
    SceneToneRequiredRule,
)
from core.knowledge_validation.rules.base import RuleContext
from core.knowledge_validation.validation_codes import BusinessRuleCode


class TestSceneParticipantsUniqueRule:
    """Tests for SC-001: participants unique."""

    def setup_method(self):
        self.rule = SceneParticipantsUniqueRule()

    def test_valid_unique_participants(self):
        entity = {
            "entity_type": "scene",
            "attributes": {
                "participants": [
                    {"character_id": "char1", "status": "present"},
                    {"character_id": "char2", "status": "present"},
                ]
            },
        }
        context = RuleContext(entity=entity, entity_type="scene")
        errors = self.rule.validate(context)
        assert len(errors) == 0

    def test_duplicate_participants(self):
        entity = {
            "entity_type": "scene",
            "attributes": {
                "participants": [
                    {"character_id": "char1", "status": "present"},
                    {"character_id": "char1", "status": "mentioned"},
                ]
            },
        }
        context = RuleContext(entity=entity, entity_type="scene")
        errors = self.rule.validate(context)
        assert len(errors) == 1
        assert errors[0].keyword == BusinessRuleCode.SC001.value


class TestSceneBoundaryTypeValidRule:
    """Tests for SC-002: boundary_type valid."""

    def setup_method(self):
        self.rule = SceneBoundaryTypeValidRule()

    def test_valid_boundary_types(self):
        for bt in ["same_scene", "scene_transition", "chapter_transition", "volume_transition", "time_skip", "perspective_shift"]:
            entity = {"entity_type": "scene", "attributes": {"boundary_type": bt}}
            context = RuleContext(entity=entity, entity_type="scene")
            errors = self.rule.validate(context)
            assert len(errors) == 0, f"Failed for boundary_type={bt}"

    def test_invalid_boundary_type(self):
        entity = {"entity_type": "scene", "attributes": {"boundary_type": "invalid"}}
        context = RuleContext(entity=entity, entity_type="scene")
        errors = self.rule.validate(context)
        assert len(errors) == 1
        assert errors[0].keyword == BusinessRuleCode.SC002.value


class TestSceneToneRequiredRule:
    """Tests for SC-003: tone required."""

    def setup_method(self):
        self.rule = SceneToneRequiredRule()

    def test_valid_tone(self):
        for tone in ["tense", "restrained", "heated", "atmospheric", "neutral", "melancholic", "joyful", "ominous", "other"]:
            entity = {"entity_type": "scene", "attributes": {"tone": tone}}
            context = RuleContext(entity=entity, entity_type="scene")
            errors = self.rule.validate(context)
            assert len(errors) == 0

    def test_missing_tone(self):
        entity = {"entity_type": "scene", "attributes": {}}
        context = RuleContext(entity=entity, entity_type="scene")
        errors = self.rule.validate(context)
        assert len(errors) == 1
        assert errors[0].keyword == BusinessRuleCode.SC003.value
    def test_invalid_tone(self):
            entity = {"entity_type": "scene", "attributes": {"tone": "invalid"}}
            context = RuleContext(entity=entity, entity_type="scene")
            errors = self.rule.validate(context)
            assert len(errors) == 1
            assert errors[0].keyword == BusinessRuleCode.SC003.value


class TestSceneSceneIdImmutableRule:
    """Tests for SC-004: scene_id immutable."""

    def setup_method(self):
        self.rule = SceneSceneIdImmutableRule()

    def test_valid_scene_id(self):
        for sid in ["SC-1", "SC-123", "SC-001"]:
            entity = {"entity_type": "scene", "attributes": {"scene_id": sid}}
            context = RuleContext(entity=entity, entity_type="scene")
            errors = self.rule.validate(context)
            assert len(errors) == 0

    def test_invalid_scene_id(self):
        for sid in ["SC", "SC-ABC", "SC-1-2", "Scene-1"]:
            entity = {"entity_type": "scene", "attributes": {"scene_id": sid}}
            context = RuleContext(entity=entity, entity_type="scene")
            errors = self.rule.validate(context)
            assert len(errors) == 1
            assert errors[0].keyword == BusinessRuleCode.SC004.value

    def test_missing_scene_id(self):
        entity = {"entity_type": "scene", "attributes": {}}
        context = RuleContext(entity=entity, entity_type="scene")
        errors = self.rule.validate(context)
        assert len(errors) == 0


class TestScenePlotPointsUniqueRule:
    """Tests for SC-005: plot_points unique."""

    def setup_method(self):
        self.rule = ScenePlotPointsUniqueRule()

    def test_valid_unique_plot_points(self):
        entity = {"entity_type": "scene", "attributes": {"plot_points": ["PP-1", "PP-2"]}}
        context = RuleContext(entity=entity, entity_type="scene")
        errors = self.rule.validate(context)
        assert len(errors) == 0

    def test_duplicate_plot_points(self):
        entity = {"entity_type": "scene", "attributes": {"plot_points": ["PP-1", "PP-1"]}}
        context = RuleContext(entity=entity, entity_type="scene")
        errors = self.rule.validate(context)
        assert len(errors) == 1
        assert errors[0].keyword == BusinessRuleCode.SC005.value


class TestSceneRulesIntegration:
    """Integration tests for all scene rules."""

    def test_all_rules_pass_valid_entity(self):
        entity = {
            "entity_type": "scene",
            "attributes": {
                "scene_id": "SC-001",
                "tone": "tense",
                "participants": [{"character_id": "char1", "status": "present"}],
                "plot_points": ["PP-1"],
                "boundary_type": "scene_transition",
            },
        }
        context = RuleContext(entity=entity, entity_type="scene")
        all_errors = []
        for rule in SCENE_RULES:
            errors = rule.validate(context)
            all_errors.extend(errors)
        assert len(all_errors) == 0