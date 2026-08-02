"""
Rule Registry
RM-5.7.3B Business Rule Validation Engine

Registry pattern for business rules. Automatically dispatches rules by domain.
"""

from core.knowledge_validation.rules.base import BaseRule
from core.knowledge_validation.rules.character_rules import CHARACTER_RULES
from core.knowledge_validation.rules.glossary_rules import GLOSSARY_RULES
from core.knowledge_validation.rules.narrative_rules import NARRATIVE_RULES
from core.knowledge_validation.rules.scene_rules import SCENE_RULES
from core.knowledge_validation.rules.style_rules import STYLE_RULES


# Rule Registry - maps domain to list of rules
RULE_REGISTRY: dict[str, list[BaseRule]] = {
    "character": CHARACTER_RULES,
    "glossary": GLOSSARY_RULES,
    "scene": SCENE_RULES,
    "narrative": NARRATIVE_RULES,
    "style": STYLE_RULES,
}


def get_rules_for_domain(domain: str) -> list[BaseRule]:
    """Get all rules for a specific domain."""
    return RULE_REGISTRY.get(domain.lower(), [])


def get_all_rules() -> list[BaseRule]:
    """Get all rules across all domains."""
    all_rules = []
    for rules in RULE_REGISTRY.values():
        all_rules.extend(rules)
    return all_rules


def get_rule_by_code(rule_code: str) -> BaseRule | None:
    """Find a rule by its code (e.g., 'CH001')."""
    for rules in RULE_REGISTRY.values():
        for rule in rules:
            if rule.rule_code.value == rule_code:
                return rule
    return None


def list_domains() -> list[str]:
    """List all registered domains."""
    return list(RULE_REGISTRY.keys())


def register_rule(domain: str, rule: BaseRule) -> None:
    """Register a custom rule for a domain."""
    domain = domain.lower()
    if domain not in RULE_REGISTRY:
        RULE_REGISTRY[domain] = []
    RULE_REGISTRY[domain].append(rule)