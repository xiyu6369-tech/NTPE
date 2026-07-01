"""Foundation-07.1 Consistency Engine."""

from __future__ import annotations

from typing import Dict, List

from .consistency import ConsistencyContract
from .contracts import ConsistencyIssue
from .memory_store import IntelligenceMemoryStore


class ConsistencyEngine:
    """Context-aware consistency validation for translated segments."""

    def __init__(self, store: IntelligenceMemoryStore) -> None:
        self.store = store
        self.contract = ConsistencyContract()

    def validate_translation(self, source_text: str, output_text: str) -> Dict[str, object]:
        issues: List[ConsistencyIssue] = []

        for entry in self.store._glossary.values():
            if entry.locked and entry.source_term in source_text and entry.target_term not in output_text:
                issues.append(
                    ConsistencyIssue(
                        code="LOCKED_GLOSSARY_TERM_NOT_APPLIED",
                        message=f"Locked glossary term was present in source but missing in output: {entry.target_term}",
                        severity="warning",
                        source=entry.source_term,
                        expected=entry.target_term,
                    )
                )

        for entry in self.store._characters.values():
            source_candidates = [entry.source_name, *entry.aliases]
            if any(candidate and candidate in source_text for candidate in source_candidates):
                if entry.target_name not in output_text:
                    issues.append(
                        ConsistencyIssue(
                            code="CHARACTER_NAME_NOT_APPLIED",
                            message=f"Character appeared in source but target name was missing: {entry.target_name}",
                            severity="warning",
                            source=entry.source_name,
                            expected=entry.target_name,
                        )
                    )

        return {
            "passed": not any(issue.severity == "error" for issue in issues),
            "issue_count": len(issues),
            "issues": [issue.to_dict() for issue in issues],
        }
