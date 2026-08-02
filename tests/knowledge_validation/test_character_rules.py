"""
Tests for Character Business Rules (CH-001 to CH-005)
RM-5.7.3B Business Rule Validation Engine
"""

import pytest

from core.knowledge_validation.rules.character_rules import (
    CHARACTER_RULES,
    CharacterAliasesNotCanonicalRule,
    CharacterCanonicalNameRule,
    CharacterConfidenceRangeRule,
    CharacterDuplicateAliasesRule,
    CharacterStatusEnumRule,
)
from core.knowledge_validation.rules.base import RuleContext
from core.knowledge_validation.validation_codes import BusinessRuleCode


class TestCharacterCanonicalNameRule:
    """Tests for CH-001: canonical_name required, cannot be empty."""

    def setup_method(self):
        self.rule = CharacterCanonicalNameRule()

    def test_valid_canonical_name(self):
        entity = {
            "entity_type": "character",
            "attributes": {"canonical_name": "John Doe"},
        }
        context = RuleContext(entity=entity, entity_type="character")
        errors = self.rule.validate(context)
        assert len(errors) == 0

    def test_missing_canonical_name(self):
        entity = {
            "entity_type": "character",
            "attributes": {},
        }
        context = RuleContext(entity=entity, entity_type="character")
        errors = self.rule.validate(context)
        assert len(errors) == 1
        assert errors[0].keyword == BusinessRuleCode.CH001.value
        assert "required" in errors[0].message.lower()

    def test_empty_canonical_name(self):
        entity = {
            "entity_type": "character",
            "attributes": {"canonical_name": ""},
        }
        context = RuleContext(entity=entity, entity_type="character")
        errors = self.rule.validate(context)
        assert len(errors) == 1

    def test_whitespace_only_canonical_name(self):
        entity = {
            "entity_type": "character",
            "attributes": {"canonical_name": "   "},
        }
        context = RuleContext(entity=entity, entity_type="character")
        errors = self.rule.validate(context)
        assert len(errors) == 1


class TestCharacterAliasesNotCanonicalRule:
    """Tests for CH-002: aliases must not contain canonical_name."""

    def setup_method(self):
        self.rule = CharacterAliasesNotCanonicalRule()

    def test_valid_aliases(self):
        entity = {
            "entity_type": "character",
            "attributes": {
                "canonical_name": "John Doe",
                "aliases": ["Johnny", "JD"],
            },
        }
        context = RuleContext(entity=entity, entity_type="character")
        errors = self.rule.validate(context)
        assert len(errors) == 0

    def test_alias_equals_canonical(self):
        entity = {
            "entity_type": "character",
            "attributes": {
                "canonical_name": "John Doe",
                "aliases": ["Johnny", "John Doe"],
            },
        }
        context = RuleContext(entity=entity, entity_type="character")
        errors = self.rule.validate(context)
        assert len(errors) == 1
        assert errors[0].keyword == BusinessRuleCode.CH002.value

    def test_alias_equals_canonical_case_insensitive(self):
        entity = {
            "entity_type": "character",
            "attributes": {
                "canonical_name": "John Doe",
                "aliases": ["john doe"],
            },
        }
        context = RuleContext(entity=entity, entity_type="character")
        errors = self.rule.validate(context)
        assert len(errors) == 1

    def test_no_canonical_name_no_error(self):
        entity = {
            "entity_type": "character",
            "attributes": {"aliases": ["Johnny"]},
        }
        context = RuleContext(entity=entity, entity_type="character")
        errors = self.rule.validate(context)
class TestCharacterDuplicateAliasesRule:
    """Tests for CH-003: duplicate aliases forbidden."""

    def setup_method(self):
        self.rule = CharacterDuplicateAliasesRule()

    def test_valid_unique_aliases(self):
        entity = {
            "entity_type": "character",
            "attributes": {"aliases": ["Johnny", "JD", "John"]},
        }
        context = RuleContext(entity=entity, entity_type="character")
        errors = self.rule.validate(context)
        assert len(errors) == 0

    def test_duplicate_aliases(self):
        entity = {
            "entity_type": "character",
            "attributes": {"aliases": ["Johnny", "Johnny", "JD"]},
        }
        context = RuleContext(entity=entity, entity_type="character")
        errors = self.rule.validate(context)
        assert len(errors) == 1
        assert errors[0].keyword == BusinessRuleCode.CH003.value

    def test_duplicate_aliases_case_insensitive(self):
        entity = {
            "entity_type": "character",
            "attributes": {"aliases": ["Johnny", "johnny"]},
        }
        context = RuleContext(entity=entity, entity_type="character")
        errors = self.rule.validate(context)
        assert len(errors) == 1


class TestCharacterConfidenceRangeRule:
    """Tests for CH-004: confidence must satisfy 0 ≤ confidence ≤ 1."""

    def setup_method(self):
        self.rule = CharacterConfidenceRangeRule()

    def test_valid_confidence(self):
        for conf in [0.0, 0.5, 1.0, 0, 1]:
            entity = {"entity_type": "character", "confidence": conf}
            context = RuleContext(entity=entity, entity_type="character")
            errors = self.rule.validate(context)
            assert len(errors) == 0, f"Failed for confidence={conf}"

    def test_confidence_below_zero(self):
        entity = {"entity_type": "character", "confidence": -0.1}
        context = RuleContext(entity=entity, entity_type="character")
        errors = self.rule.validate(context)
        assert len(errors) == 1
        assert errors[0].keyword == BusinessRuleCode.CH004.value

    def test_confidence_above_one(self):
        entity = {"entity_type": "character", "confidence": 1.5}
        context = RuleContext(entity=entity, entity_type="character")
        errors = self.rule.validate(context)
        assert len(errors) == 1

    def test_invalid_confidence_type(self):
        entity = {"entity_type": "character", "confidence": "high"}
        context = RuleContext(entity=entity, entity_type="character")
        errors = self.rule.validate(context)
        assert len(errors) == 1

    def test_none_confidence(self):
        entity = {"entity_type": "character", "confidence": None}
        context = RuleContext(entity=entity, entity_type="character")
        errors = self.rule.validate(context)
        assert len(errors) == 0


class TestCharacterStatusEnumRule:
    """Tests for CH-005: status must be one of schema enum."""

    def setup_method(self):
        self.rule = CharacterStatusEnumRule()

    def test_valid_statuses(self):
        for status in ["pending", "approved", "rejected", "needs_review"]:
            entity = {
                "entity_type": "character",
                "metadata": {"review_status": status},
            }
            context = RuleContext(entity=entity, entity_type="character")
            errors = self.rule.validate(context)
            assert len(errors) == 0, f"Failed for status={status}"

    def test_invalid_status(self):
        entity = {
            "entity_type": "character",
            "metadata": {"review_status": "invalid_status"},
        }
        context = RuleContext(entity=entity, entity_type="character")
        errors = self.rule.validate(context)
        assert len(errors) == 1
        assert errors[0].keyword == BusinessRuleCode.CH005.value

    def test_missing_status(self):
        entity = {"entity_type": "character", "metadata": {}}
        context = RuleContext(entity=entity, entity_type="character")
        errors = self.rule.validate(context)
        assert len(errors) == 0


class TestCharacterRulesIntegration:
    """Integration tests for all character rules."""

    def test_all_rules_pass_valid_entity(self):
        entity = {
            "entity_type": "character",
            "name": "John Doe",
            "attributes": {
                "canonical_name": "John Doe",
                "aliases": ["Johnny", "JD"],
                "role": "protagonist",
            },
            "confidence": 0.9,
            "metadata": {"review_status": "approved"},
        }
        context = RuleContext(entity=entity, entity_type="character")
        all_errors = []
        for rule in CHARACTER_RULES:
            errors = rule.validate(context)
            all_errors.extend(errors)
        assert len(all_errors) == 0

    def test_multiple_violations(self):
        entity = {
            "entity_type": "character",
            "attributes": {
                "canonical_name": "",
                "aliases": ["John", "John"],
            },
            "confidence": 1.5,
            "metadata": {"review_status": "invalid"},
        }
        context = RuleContext(entity=entity, entity_type="character")
        all_errors = []
        for rule in CHARACTER_RULES:
            errors = rule.validate(context)
            all_errors.extend(errors)
        assert len(all_errors) == 4  # CH001, CH003, CH004, CH005
        codes = {e.keyword for e in all_errors}
        assert BusinessRuleCode.CH001.value in codes
        assert BusinessRuleCode.CH003.value in codes
        assert BusinessRuleCode.CH004.value in codes
        assert BusinessRuleCode.CH005.value in codes