from __future__ import annotations

from .contract import QualityComponent, QualityContext, QualityIssue, QualityResult


class ConsistencyValidator(QualityComponent):
    name = "consistency_validator"

    def run(self, context: QualityContext, result: QualityResult) -> QualityResult:
        text = result.text or context.translated_text or ""
        mappings = {}
        mappings.update(context.glossary or {})
        mappings.update(context.character_names or {})
        for source, target in mappings.items():
            if source and source in (context.source_text or "") and target and target not in text:
                result.add_issue(QualityIssue("MISSING_LOCKED_TERM", f"missing locked term: {target}", "error", suggestion=target, metadata={"source": source, "target": target}))
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        seen = {}
        for line in lines:
            seen[line] = seen.get(line, 0) + 1
            if seen[line] >= 3 and len(line) > 8:
                result.add_issue(QualityIssue("REPEATED_LINE", "repeated line detected", "error", metadata={"line": line}))
                break
        return result
