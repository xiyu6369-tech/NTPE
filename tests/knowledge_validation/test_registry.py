"""
Tests for Rule Registry
RM-5.7.3B Business Rule Validation Engine
"""

import pytest

from core.knowledge_validation.rules.registry import (
    get_all_rules,
    get_rule_by_code,
    get_rules_for_domain,
    list_domains,
    register_rule,
    RULE_REGISTRY,
)
from core.knowledge_validation.rules.base import BaseRule, EntityRule
from core.knowledge_validation.validation_codes import BusinessRuleCode


class TestRuleRegistry:
    """Tests for the rule registry."""

    def test_all_domains_registered(self):
        domains = list_domains()
        assert "character" in domains
        assert "glossary" in domains
        assert "scene" in domains
        assert "narrative" in domains
        assert "style" in domains
        assert len(domains) == 5

    def test_get_rules_for_domain(self):
        char_rules = get_rules_for_domain("character")
        assert len(char_rules) == 5
        assert all(isinstance(r, BaseRule) for r in char_rules)

        glossary_rules = get_rules_for_domain("glossary")
        assert len(glossary_rules) == 5

        scene_rules = get_rules_for_domain("scene")
        assert len(scene_rules) == 5

        narrative_rules = get_rules_for_domain("narrative")
        assert len(narrative_rules) == 5

        style_rules = get_rules_for_domain("style")
        assert len(style_rules) == 5

    def test_get_rules_for_unknown_domain(self):
        rules = get_rules_for_domain("unknown")
        assert rules == []

    def test_get_all_rules(self):
        all_rules = get_all_rules()
        assert len(all_rules) == 25  # 5 domains * 5 rules each

    def test_get_rule_by_code(self):
        rule = get_rule_by_code("CH001")
        assert rule is not None
        assert rule.rule_code == BusinessRuleCode.CH001

        rule = get_rule_by_code("GL003")
        assert rule is not None
        assert rule.rule_code == BusinessRuleCode.GL003

        rule = get_rule_by_code("INVALID")
        assert rule is None

    def test_register_custom_rule(self):
        initial_count = len(get_rules_for_domain("custom"))
        
        class CustomRule(EntityRule):
            @property
            def domain(self):
                return "custom"
            
            def _validate_entity(self, entity, context):
                return []
        
        custom_rule = CustomRule(BusinessRuleCode.CH001)  # Reuse code for test
        register_rule("custom", custom_rule)
        
        rules = get_rules_for_domain("custom")
        assert len(rules) == initial_count + 1
        assert rules[-1] is custom_rule