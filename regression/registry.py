"""Regression baseline registry."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Iterable
from .baseline import BaselineComponent, RegressionBaseline

@dataclass
class RegressionRegistry:
    components: Dict[str, BaselineComponent] = field(default_factory=dict)

    @classmethod
    def default(cls) -> "RegressionRegistry":
        baseline = RegressionBaseline.default()
        return cls({component.name: component for component in baseline.components})

    def register(self, component: BaselineComponent) -> None:
        self.components[component.name] = component

    def require(self, name: str) -> BaselineComponent:
        if name not in self.components:
            raise KeyError(f"Regression component not registered: {name}")
        return self.components[name]

    def names(self) -> list[str]:
        return list(self.components.keys())

    def validate(self) -> Dict[str, object]:
        baseline = RegressionBaseline(list(self.components.values()))
        return baseline.validate()

    def to_baseline(self) -> RegressionBaseline:
        return RegressionBaseline(list(self.components.values()))
