from __future__ import annotations

from .feedback_adapter import AdaptiveFeedbackAdapter
from .policy import POLICY_VERSION, render_generation_policy, unified_discipline_rules
from .profile import normalize_discipline_profile
from .registry import DisciplineRuleRegistry
from .report import build_discipline_report

ENGINE_VERSION = "6.0.0"


class TranslationDisciplineEngine:
    def __init__(self, profile: str | None = None, registry: DisciplineRuleRegistry | None = None) -> None:
        self.profile = normalize_discipline_profile(profile)
        self.registry = registry or DisciplineRuleRegistry(unified_discipline_rules())
        self.feedback = AdaptiveFeedbackAdapter(self.registry)

    def active_rules(self, *, enabled: bool = True):
        return self.registry.active(self.profile) if enabled else ()

    def generation_rules(self, *, enabled: bool = True):
        return tuple(rule for rule in self.active_rules(enabled=enabled) if rule.phase == "generation")

    def render_generation_policy(self, *, enabled: bool = True) -> str:
        return render_generation_policy(self.generation_rules(enabled=enabled))

    def adaptive_rules(self, issue_codes=(), *, enabled: bool = True):
        return self.feedback.map_issue_codes(issue_codes) if enabled else ()

    def metadata(self, *, enabled: bool = True, adaptive_issue_codes=()) -> dict[str, object]:
        rules = self.active_rules(enabled=enabled)
        adaptive = self.adaptive_rules(adaptive_issue_codes, enabled=enabled)
        return {
            "discipline_engine_version": ENGINE_VERSION,
            "discipline_policy_version": POLICY_VERSION,
            "discipline_policy_source": "core.translation_discipline",
            "discipline_profile": self.profile,
            "active_rule_codes": [rule.code for rule in rules],
            "active_rule_count": len(rules),
            "generation_rule_count": sum(rule.phase == "generation" for rule in rules),
            "adaptive_rule_codes": [rule.code for rule in adaptive],
            "adaptive_rule_count": len(adaptive),
        }

    def report(self, *, enabled: bool = True) -> dict[str, object]:
        rules = self.active_rules(enabled=enabled)
        return build_discipline_report(
            self.profile,
            rules,
            legacy_mappings={rule.code: rule.code for rule in rules},
        )
