"""Consistency checks for Foundation-07.0 intelligence contracts."""

from __future__ import annotations

from typing import Iterable, List

from .contracts import ConsistencyIssue, GlossaryEntry


class ConsistencyContract:
    """Validates whether locked intelligence terms are respected in output text."""

    def validate_glossary_output(self, output_text: str, glossary: Iterable[GlossaryEntry]) -> List[ConsistencyIssue]:
        issues: List[ConsistencyIssue] = []
        for entry in glossary:
            if not entry.locked:
                continue
            if entry.target_term and entry.target_term not in output_text:
                issues.append(
                    ConsistencyIssue(
                        code="LOCKED_TERM_MISSING",
                        message=f"Locked glossary target term is missing: {entry.target_term}",
                        severity="warning",
                        source=entry.source_term,
                        expected=entry.target_term,
                    )
                )
        return issues

    def validate_character_output(self, output_text: str, target_names: Iterable[str]) -> List[ConsistencyIssue]:
        issues: List[ConsistencyIssue] = []
        for name in target_names:
            if name and name not in output_text:
                issues.append(
                    ConsistencyIssue(
                        code="CHARACTER_NAME_MISSING",
                        message=f"Expected character name is missing: {name}",
                        severity="info",
                        expected=name,
                    )
                )
        return issues
