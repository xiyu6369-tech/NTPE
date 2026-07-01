from __future__ import annotations

from .contract import QualityComponent, QualityContext, QualityResult


class RepairEngine(QualityComponent):
    name = "repair_engine"

    def run(self, context: QualityContext, result: QualityResult) -> QualityResult:
        text = result.text or context.translated_text or ""
        for source, target in {**(context.glossary or {}), **(context.character_names or {})}.items():
            if source and target:
                text = text.replace(source, target)
        # collapse exact adjacent duplicate lines
        repaired_lines = []
        previous = None
        for line in text.splitlines():
            if line.strip() and line == previous:
                result.repairs.append("duplicate_line_removed")
                continue
            repaired_lines.append(line)
            previous = line
        result.text = "\n".join(repaired_lines)
        if result.repairs:
            result.metadata["repaired"] = True
        return result
