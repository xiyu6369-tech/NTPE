from __future__ import annotations

import re
from .contract import QualityComponent, QualityContext, QualityIssue, QualityResult


class SemanticValidator(QualityComponent):
    name = "semantic_validator"

    def run(self, context: QualityContext, result: QualityResult) -> QualityResult:
        source = context.source_text or ""
        text = result.text or context.translated_text or ""
        if source.strip() and not text.strip():
            result.add_issue(QualityIssue("EMPTY_TRANSLATION", "translation is empty", "critical"))
        if len(source) > 0 and len(text) < max(5, int(len(source) * 0.08)):
            result.add_issue(QualityIssue("TOO_SHORT", "translation appears too short", "error"))
        korean_left = re.findall(r"[\uac00-\ud7af]", text)
        if len(korean_left) >= 3:
            result.add_issue(QualityIssue("KOREAN_RESIDUE", "translated text contains Korean residue", "error", metadata={"count": len(korean_left)}))
        return result
