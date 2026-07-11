from __future__ import annotations

from collections.abc import Iterable
from .registry import DisciplineRuleRegistry
from .rule import DisciplineRule

_ISSUE_RULE = {"EMPTY_OUTPUT": "NO_SUMMARIZATION", "TOO_SHORT": "NO_SUMMARIZATION", "PARAGRAPH_OMISSION_SUSPECTED": "PRESERVE_PARAGRAPH_INTENT", "SENTENCE_OMISSION_SUSPECTED": "NO_SUMMARIZATION", "DUPLICATE_LINE": "NO_PREVIOUS_RESTATEMENT", "DUPLICATE_SENTENCE": "NO_PREVIOUS_RESTATEMENT", "DUPLICATE_PARAGRAPH": "NO_PREVIOUS_RESTATEMENT", "SEMANTIC_DUPLICATE_PARAGRAPH": "NO_PREVIOUS_RESTATEMENT", "ADDED_DETAIL": "NO_ADDED_PLOT", "HALLUCINATION": "NO_ADDED_PLOT", "QUALITY_LOCK_VIOLATION": "PREVIOUS_CONTEXT_ONLY", "CHARACTER_VOICE_DRIFT": "PRESERVE_PARAGRAPH_INTENT", "HONORIFIC_REGISTER_DRIFT": "PRESERVE_PARAGRAPH_INTENT", "RELATIONSHIP_DISTANCE_DRIFT": "PRESERVE_PARAGRAPH_INTENT", "NARRATIVE_VIEWPOINT_DRIFT": "PRESERVE_PARAGRAPH_INTENT", "NARRATIVE_REGISTER_DRIFT": "PRESERVE_PARAGRAPH_INTENT", "ERA_INAPPROPRIATE_EXPRESSION": "PRESERVE_PARAGRAPH_INTENT", "DIALOGUE_NARRATION_REGISTER_MIX": "PRESERVE_PARAGRAPH_INTENT", "UNSUPPORTED_EMOTIONAL_AMPLIFICATION": "NO_ADDED_PSYCHOLOGY"}


class AdaptiveFeedbackAdapter:
    def __init__(self, registry: DisciplineRuleRegistry) -> None:
        self.registry = registry

    def map_issue_code(self, code: str) -> DisciplineRule | None:
        canonical = str(code).strip().upper()
        if canonical.startswith("V5_"):
            canonical = canonical[3:]
        return self.registry.get(_ISSUE_RULE.get(canonical, canonical))

    def map_issue_codes(self, codes: Iterable[str]) -> tuple[DisciplineRule, ...]:
        found: list[DisciplineRule] = []
        for code in codes:
            rule = self.map_issue_code(code)
            if rule and rule not in found:
                found.append(rule)
        return tuple(found)
