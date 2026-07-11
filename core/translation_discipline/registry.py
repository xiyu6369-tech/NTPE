from __future__ import annotations

from collections.abc import Iterable
from .rule import DisciplineRule


class DisciplineRuleRegistry:
    def __init__(self, rules: Iterable[DisciplineRule] = ()) -> None:
        self._rules: dict[str, DisciplineRule] = {}
        for rule in rules:
            self.register(rule)

    def register(self, rule: DisciplineRule) -> None:
        if rule.code in self._rules:
            raise ValueError(f"duplicate discipline rule code: {rule.code}")
        self._rules[rule.code] = rule

    def get(self, code: str) -> DisciplineRule | None:
        return self._rules.get(str(code).strip().upper())

    def all(self) -> tuple[DisciplineRule, ...]:
        return tuple(self._rules.values())

    def active(self, profile: str) -> tuple[DisciplineRule, ...]:
        return tuple(rule for rule in self._rules.values() if rule.enabled and (not rule.profiles or profile in rule.profiles))
