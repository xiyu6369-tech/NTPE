"""
Tests for Glossary Business Rules (GL-001 to GL-005)
RM-5.7.3B Business Rule Validation Engine
"""

import pytest

from core.knowledge_validation.rules.glossary_rules import (
    GLOSSARY_RULES,
    GlossaryAliasDuplicatesRule,
    GlossaryConfidenceRangeRule,
    GlossaryForbiddenFormsRule,
    GlossaryLockedImmutableRule,
    GlossarySourceUniqueRule,
)
from core.knowledge_validation.rules.base import RuleContext
from core.knowledge_validation.validation_codes import BusinessRuleCode


class TestGlossarySourceUniqueRule:
    """Tests for GL-001: source unique."""

    def setup_method(self):
        self.rule = GlossarySourceUniqueRule()

    def test_unique_sources(self):
        entities = [
            {"entity_type": "glossary", "name": "术语1", "attributes": {"canonical_translation": "Term 1"}},
            {"entity_type": "glossary", "name": "术语2", "attributes": {"canonical_translation": "Term 2"}},
        ]
        context = RuleContext(entity={}, entity_type="glossary", all_entities={"glossary": entities})
        errors = self.rule.validate(context)
        assert len(errors) == 0

    def test_duplicate_source(self):
        entities = [
            {"entity_type": "glossary", "name": "术语1", "attributes": {"canonical_translation": "Term 1"}},
            {"entity_type": "glossary", "name": "术语1", "attributes": {"canonical_translation": "Term 1 Duplicate"}},
        ]
        context = RuleContext(entity={}, entity_type="glossary", all_entities={"glossary": entities})
        errors = self.rule.validate(context)
        assert len(errors) == 1
        assert errors[0].keyword == BusinessRuleCode.GL001.value


class TestGlossaryLockedImmutableRule:
    """Tests for GL-002: locked term immutable."""

    def setup_method(self):
        self.rule = GlossaryLockedImmutableRule()

    def test_locked_with_translation(self):
        entity = {
            "entity_type": "glossary",
            "name": "术语",
            "attributes": {"canonical_translation": "Term"},
            "metadata": {"lock_status": "locked"},
        }
        context = RuleContext(entity=entity, entity_type="glossary")
        errors = self.rule.validate(context)
        assert len(errors) == 0

    def test_locked_without_translation(self):
        entity = {
            "entity_type": "glossary",
            "name": "术语",
            "attributes": {},
            "metadata": {"lock_status": "locked"},
        }
        context = RuleContext(entity=entity, entity_type="glossary")
        errors = self.rule.validate(context)
        assert len(errors) == 1
        assert errors[0].keyword == BusinessRuleCode.GL002.value

    def test_unlocked_no_error(self):
        entity = {
            "entity_type": "glossary",
            "name": "术语",
            "attributes": {},
            "metadata": {"lock_status": "unlocked"},
        }
        context = RuleContext(entity=entity, entity_type="glossary")
        errors = self.rule.validate(context)
        assert len(errors) == 0
class TestGlossaryForbiddenFormsRule:
    """Tests for GL-003: forbidden_forms cannot contain target."""

    def setup_method(self):
        self.rule = GlossaryForbiddenFormsRule()

    def test_valid_forbidden_forms(self):
        entity = {
            "entity_type": "glossary",
            "attributes": {
                "canonical_translation": "Term",
                "forbidden_forms": ["Wrong1", "Wrong2"],
            },
        }
        context = RuleContext(entity=entity, entity_type="glossary")
        errors = self.rule.validate(context)
        assert len(errors) == 0

    def test_forbidden_contains_target(self):
        entity = {
            "entity_type": "glossary",
            "attributes": {
                "canonical_translation": "Term",
                "forbidden_forms": ["Wrong1", "Term"],
            },
        }
        context = RuleContext(entity=entity, entity_type="glossary")
        errors = self.rule.validate(context)
        assert len(errors) == 1
        assert errors[0].keyword == BusinessRuleCode.GL003.value


class TestGlossaryAliasDuplicatesRule:
    """Tests for GL-004: alias duplicates forbidden."""

    def setup_method(self):
        self.rule = GlossaryAliasDuplicatesRule()

    def test_valid_unique_aliases(self):
        entity = {
            "entity_type": "glossary",
            "attributes": {"aliases": ["alias1", "alias2"]},
        }
        context = RuleContext(entity=entity, entity_type="glossary")
        errors = self.rule.validate(context)
        assert len(errors) == 0

    def test_duplicate_aliases(self):
        entity = {
            "entity_type": "glossary",
            "attributes": {"aliases": ["alias1", "alias1"]},
        }
        context = RuleContext(entity=entity, entity_type="glossary")
        errors = self.rule.validate(context)
        assert len(errors) == 1
        assert errors[0].keyword == BusinessRuleCode.GL004.value


class TestGlossaryConfidenceRangeRule:
    """Tests for GL-005: confidence range."""

    def setup_method(self):
        self.rule = GlossaryConfidenceRangeRule()

    def test_valid_confidence(self):
        for conf in [0.0, 0.5, 1.0]:
            entity = {"entity_type": "glossary", "confidence": conf}
            context = RuleContext(entity=entity, entity_type="glossary")
            errors = self.rule.validate(context)
            assert len(errors) == 0

    def test_invalid_confidence(self):
        entity = {"entity_type": "glossary", "confidence": 1.5}
        context = RuleContext(entity=entity, entity_type="glossary")
        errors = self.rule.validate(context)
        assert len(errors) == 1
        assert errors[0].keyword == BusinessRuleCode.GL005.value


class TestGlossaryRulesIntegration:
    """Integration tests for all glossary rules."""

    def test_all_rules_pass_valid_entities(self):
        entities = [
            {
                "entity_type": "glossary",
                "name": "术语1",
                "attributes": {
                    "canonical_translation": "Term 1",
                    "aliases": ["a1"],
                    "forbidden_forms": ["wrong"],
                },
                "confidence": 0.9,
                "metadata": {"lock_status": "unlocked"},
            },
            {
                "entity_type": "glossary",
                "name": "术语2",
                "attributes": {
                    "canonical_translation": "Term 2",
                },
                "confidence": 0.8,
                "metadata": {"lock_status": "locked"},
            },
        ]
        all_errors = []
        for entity in entities:
            context = RuleContext(entity=entity, entity_type="glossary", all_entities={"glossary": entities})
            for rule in GLOSSARY_RULES:
                errors = rule.validate(context)
                all_errors.extend(errors)
        assert len(all_errors) == 0