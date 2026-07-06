# =====================================================
# NTPE 1.2 Professional
# Stage-15.7 Quality Auto Repair Layer
# =====================================================

from __future__ import annotations

import re
from typing import Iterable

from .quality_context import QualityContext
from .quality_result import QualityResult
from .repair_policy import QualityRepairPolicy
from .repair_result import RepairAction, RepairResult, RepairStatus

_PLACEHOLDER_PATTERN = re.compile(r"\{[^{}]+\}|%\w|\$\{[^{}]+\}")


def _placeholders(text: str) -> set[str]:
    return set(_PLACEHOLDER_PATTERN.findall(text or ""))


class QualityAutoRepairEngine:
    """Deterministic quality repair layer.

    Stage-15.7 repairs only defects that can be fixed without changing story
    content: whitespace, line endings, duplicate consecutive lines, dialogue
    quote style, and explicit glossary replacement.
    """

    stage = "Stage-15.7"

    def __init__(self, policy: QualityRepairPolicy | None = None) -> None:
        self.policy = policy or QualityRepairPolicy()

    def repair(
        self,
        context: QualityContext,
        quality_result: QualityResult | None = None,
    ) -> RepairResult:
        original = context.translated_text or ""
        text = original
        result = RepairResult(original_text=original, repaired_text=original)

        source_ph = _placeholders(context.source_text or "") if self.policy.preserve_placeholders else set()

        text = self._normalize_line_endings(text, result)
        text = self._trim_trailing_whitespace(text, result)
        text = self._collapse_blank_lines(text, result)
        text = self._collapse_duplicate_lines(text, result)
        text = self._normalize_dialogue_quotes(text, result)
        text = self._apply_glossary(text, result)

        if self.policy.preserve_placeholders and not source_ph.issubset(_placeholders(text)):
            # Revert if a repair accidentally loses a source placeholder.
            return RepairResult(
                original_text=original,
                repaired_text=original,
                status=RepairStatus.SKIPPED,
                actions=[],
                metadata={"reason": "placeholder_preservation_guard"},
            )

        result.repaired_text = text
        result.status = RepairStatus.REPAIRED if result.changed else RepairStatus.CLEAN
        if quality_result is not None:
            result.metadata["input_quality_status"] = quality_result.status.value
            result.metadata["input_issue_count"] = len(quality_result.issues)
        return result

    def repair_text(
        self,
        source_text: str,
        translated_text: str,
        *,
        language_pair: str = "ko->zh-TW",
        **metadata: object,
    ) -> RepairResult:
        return self.repair(
            QualityContext(
                source_text=source_text,
                translated_text=translated_text,
                language_pair=language_pair,
                metadata=dict(metadata),
            )
        )

    def _record(self, result: RepairResult, name: str, category: str, description: str, before: str, after: str, **metadata: object) -> None:
        if before != after:
            result.add_action(
                RepairAction(
                    name=name,
                    category=category,
                    description=description,
                    before_length=len(before),
                    after_length=len(after),
                    metadata=dict(metadata),
                )
            )

    def _normalize_line_endings(self, text: str, result: RepairResult) -> str:
        if not self.policy.normalize_line_endings:
            return text
        before = text
        after = text.replace("\r\n", "\n").replace("\r", "\n")
        self._record(result, "normalize_line_endings", "formatting", "Normalize CRLF/CR line endings to LF.", before, after)
        return after

    def _trim_trailing_whitespace(self, text: str, result: RepairResult) -> str:
        if not self.policy.trim_trailing_whitespace:
            return text
        before = text
        after = "\n".join(line.rstrip() for line in text.split("\n"))
        self._record(result, "trim_trailing_whitespace", "formatting", "Trim trailing whitespace from each line.", before, after)
        return after

    def _collapse_blank_lines(self, text: str, result: RepairResult) -> str:
        if not self.policy.collapse_excess_blank_lines:
            return text
        before = text
        max_blank = max(1, int(self.policy.max_blank_lines))
        pattern = re.compile(r"\n{" + str(max_blank + 2) + r",}")
        after = pattern.sub("\n" * (max_blank + 1), text)
        self._record(result, "collapse_excess_blank_lines", "structure", "Collapse excessive blank lines while preserving paragraph breaks.", before, after, max_blank_lines=max_blank)
        return after

    def _collapse_duplicate_lines(self, text: str, result: RepairResult) -> str:
        if not self.policy.collapse_consecutive_duplicate_lines:
            return text
        before = text
        out: list[str] = []
        removed = 0
        previous_normalized = None
        for line in text.split("\n"):
            normalized = line.strip()
            if normalized and previous_normalized == normalized:
                removed += 1
                continue
            out.append(line)
            previous_normalized = normalized if normalized else None
        after = "\n".join(out)
        self._record(result, "collapse_consecutive_duplicate_lines", "repetition", "Remove consecutive duplicate non-empty lines.", before, after, removed_lines=removed)
        return after

    def _normalize_dialogue_quotes(self, text: str, result: RepairResult) -> str:
        if not self.policy.normalize_dialogue_quotes:
            return text
        before = text
        # Conservative conversion only for balanced straight/double CJK-ish dialogue fragments.
        after = re.sub(r'"([^"\n]{1,160})"', r'「\1」', text)
        self._record(result, "normalize_dialogue_quotes", "formatting", "Normalize balanced straight dialogue quotes to Taiwanese corner quotes.", before, after)
        return after

    def _apply_glossary(self, text: str, result: RepairResult) -> str:
        if not self.policy.apply_glossary_terms or not self.policy.glossary:
            return text
        before = text
        after = text
        replacements = 0
        for wrong, correct in sorted(self.policy.glossary.items(), key=lambda item: len(item[0]), reverse=True):
            if not wrong or wrong == correct:
                continue
            count = after.count(wrong)
            if count:
                after = after.replace(wrong, correct)
                replacements += count
        self._record(result, "apply_glossary_terms", "terminology", "Apply explicit glossary replacements.", before, after, replacements=replacements)
        return after


def repair_translation_text(source_text: str, translated_text: str, glossary: dict[str, str] | None = None) -> str:
    policy = QualityRepairPolicy(glossary=glossary or {})
    return QualityAutoRepairEngine(policy).repair_text(source_text, translated_text).repaired_text
