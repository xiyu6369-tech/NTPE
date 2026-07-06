# =====================================================
# NTPE 1.2 Professional
# Stage-15.7 Quality Auto Repair Layer
# =====================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class QualityRepairPolicy:
    """Safe, deterministic repair policy for Stage-15 TQE.

    The policy intentionally avoids creative rewriting. It only applies
    structural, terminology, whitespace, duplicate-line, quote, and
    placeholder-safe transformations.
    """

    normalize_line_endings: bool = True
    trim_trailing_whitespace: bool = True
    collapse_excess_blank_lines: bool = True
    normalize_dialogue_quotes: bool = True
    collapse_consecutive_duplicate_lines: bool = True
    apply_glossary_terms: bool = True
    preserve_placeholders: bool = True
    max_blank_lines: int = 2
    glossary: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def conservative(cls) -> "QualityRepairPolicy":
        return cls(
            normalize_line_endings=True,
            trim_trailing_whitespace=True,
            collapse_excess_blank_lines=True,
            normalize_dialogue_quotes=False,
            collapse_consecutive_duplicate_lines=True,
            apply_glossary_terms=True,
            preserve_placeholders=True,
        )
