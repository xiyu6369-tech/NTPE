"""
Tests for Business Rule Validator
RM-5.7.3B Business Rule Validation Engine
"""

import pytest

from core.knowledge_validation.business_validator import BusinessRuleValidator, BusinessValidationSummary
from core.knowledge_validation.validation_result import ValidationResult
from core.knowledge_validation.validation_codes import BusinessRuleCode


class TestBusinessRuleValidator:
    """Tests for BusinessRuleValidator."""

    def setup_method(self):
        self.validator = BusinessRuleValidator()

    def test_validate_valid_character(self):
        entity = {
            "entity_type": "character",
            "attributes": {
                "canonical_name": "John Doe",
                "aliases": ["Johnny"],
            },
            "confidence": 0.9,
            "metadata": {"review_status": "approved"},
        }
        result = self.validator.validate(entity)
        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert result.schema == "business_rules.character"

    def test_validate_invalid_character_missing_canonical(self):
        entity = {
            "entity_type": "character",
            "attributes": {},
            "confidence": 0.9,
        }
        result = self.validator.validate(entity)
        assert result.valid is False
        assert result.error_count > 0
        codes = {e.keyword for e in result.errors}
        assert BusinessRuleCode.CH001.value in codes

    def test_validate_with_explicit_domain(self):
        entity = {
            "entity_type": "character",
            "attributes": {"canonical_name": "John"},
            "confidence": 0.5,
        }
        result = self.validator.validate(entity, domain="character")
        assert result.valid is True

    def test_validate_unknown_domain(self):
        entity = {"entity_type": "unknown"}
        result = self.validator.validate(entity)
        assert result.valid is True
        assert result.metadata.get("skipped") is True

    def test_validate_many_characters(self):
        entities = [
            {"entity_type": "character", "attributes": {"canonical_name": "John"}, "confidence": 0.9},
            {"entity_type": "character", "attributes": {"canonical_name": "Jane"}, "confidence": 0.8},
        ]
        results = self.validator.validate_many(entities, domain="character")
        assert len(results) == 2
        assert all(r.valid for r in results)

    def test_validate_many_with_violations(self):
        entities = [
            {"entity_type": "character", "attributes": {"canonical_name": "John"}, "confidence": 0.9},
            {"entity_type": "character", "attributes": {}, "confidence": 1.5},  # Invalid
        ]
        results = self.validator.validate_many(entities, domain="character")
        assert len(results) == 2
        assert results[0].valid is True
        assert results[1].valid is False

    def test_validate_domain_character(self):
        entities = [
            {"entity_type": "character", "attributes": {"canonical_name": "John"}, "confidence": 0.9},
            {"entity_type": "character", "attributes": {"canonical_name": "Jane"}, "confidence": 0.8},
        ]
        result = self.validator.validate_domain("character", entities)
        assert result.valid is True

    def test_validate_domain_with_cross_entity_rule(self):
        """Test GL-001 (source unique) which is a cross-entity rule."""
        entities = [
            {"entity_type": "glossary", "name": "术语1", "attributes": {"canonical_translation": "Term 1"}},
            {"entity_type": "glossary", "name": "术语1", "attributes": {"canonical_translation": "Term 1 Dup"}},  # Duplicate
        ]
        result = self.validator.validate_domain("glossary", entities)
        assert result.valid is False
        codes = {e.keyword for e in result.errors}
        assert BusinessRuleCode.GL001.value in codes

    def test_validate_all_domains(self):
        entities_by_domain = {
            "character": [
                {"entity_type": "character", "attributes": {"canonical_name": "John"}, "confidence": 0.9}
            ],
            "glossary": [
                {"entity_type": "glossary", "name": "术语", "attributes": {"canonical_translation": "Term"}, "confidence": 0.8}
            ],
            "unknown_domain": [
                {"entity_type": "unknown"}
            ],
        }
        results = self.validator.validate_all_domains(entities_by_domain)
        assert "character" in results
        assert "glossary" in results
        assert "unknown_domain" in results
        assert results["character"].valid is True
        assert results["glossary"].valid is True
        assert results["unknown_domain"].metadata.get("skipped") is True

    def test_get_summary(self):
        entities_by_domain = {
            "character": [
                {"entity_type": "character", "attributes": {"canonical_name": "John"}, "confidence": 0.9},
                {"entity_type": "character", "attributes": {}, "confidence": 1.5},  # CH001, CH004
            ],
        }
        results = self.validator.validate_all_domains(entities_by_domain)
        summary = self.validator.get_summary(results)
        
        assert summary.total_errors == 2
        assert "character" in summary.domains_validated
        assert summary.errors_by_domain["character"] == 2
        assert BusinessRuleCode.CH001.value in summary.errors_by_code
        assert BusinessRuleCode.CH004.value in summary.errors_by_code

    def test_strict_mode(self):
        """Test that strict_mode parameter is accepted."""
        validator = BusinessRuleValidator(strict_mode=False)
        assert validator.strict_mode is False
        
        validator = BusinessRuleValidator(strict_mode=True)
        assert validator.strict_mode is True