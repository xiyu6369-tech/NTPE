from __future__ import annotations

from typing import Iterable, List
from .contract import QualityComponent, QualityContext, QualityResult
from .semantic_validator import SemanticValidator
from .consistency_validator import ConsistencyValidator
from .style_enforcer import StyleEnforcer
from .repair_engine import RepairEngine
from .scorer import QualityScorer


class QualityPipeline:
    def __init__(self, components: Iterable[QualityComponent] | None = None):
        self.components: List[QualityComponent] = list(components) if components is not None else [
            StyleEnforcer(),
            RepairEngine(),
            SemanticValidator(),
            ConsistencyValidator(),
            QualityScorer(),
        ]

    def run(self, context: QualityContext) -> QualityResult:
        result = QualityResult(text=context.translated_text)
        for component in self.components:
            result = component.run(context, result)
        result.metadata.setdefault("pipeline", self.manifest())
        return result

    def manifest(self):
        return {"name": "translation_quality_pipeline", "components": [component.name for component in self.components]}
