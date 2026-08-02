"""
Business Rules Package
RM-5.7.3B Business Rule Validation Engine

Exports all business rule modules and the rule registry.
"""

from core.knowledge_validation.rules.base import BaseRule, EntityRule, DomainRule, RuleContext
from core.knowledge_validation.rules.character_rules import CHARACTER_RULES
from core.knowledge_validation.rules.glossary_rules import GLOSSARY_RULES
from core.knowledge_validation.rules.narrative_rules import NARRATIVE_RULES
from core.knowledge_validation.rules.registry import (
    RULE_REGISTRY,
    get_all_rules,
    get_rule_by_code,
    get_rules_for_domain,
    list_domains,
    register_rule,
)
from core.knowledge_validation.rules.scene_rules import SCENE_RULES
from core.knowledge_validation.rules.style_rules import STYLE_RULES

__all__ = [
    "BaseRule",
    "EntityRule",
    "DomainRule",
    "RuleContext",
    "CHARACTER_RULES",
    "GLOSSARY_RULES",
    "SCENE_RULES",
    "NARRATIVE_RULES",
    "STYLE_RULES",
    "RULE_REGISTRY",
    "get_rules_for_domain",
    "get_all_rules",
    "get_rule_by_code",
    "list_domains",
    "register_rule",
]