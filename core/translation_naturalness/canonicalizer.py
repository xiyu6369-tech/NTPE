from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

NATURALNESS_CANONICALIZER_VERSION = "6.0.0-stage12.1"

# Only deterministic collocation fixes are allowed here.  No semantic guessing.
_LITERAL_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("普通的觀光客人", "普通觀光客"),
    ("普通觀光客人", "普通觀光客"),
    ("穿著膝蓋的短褲", "穿著及膝短褲"),
    ("膝蓋長度的短褲", "及膝短褲"),
    ("秘書般的人物", "秘書模樣的人"),
    ("秘書般的人", "秘書模樣的人"),
)


@dataclass(frozen=True)
class CanonicalizationResult:
    text: str
    changed: bool
    actions: tuple[dict[str, Any], ...] = ()
    warnings: tuple[dict[str, Any], ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "version": NATURALNESS_CANONICALIZER_VERSION,
            "changed": self.changed,
            "actions": [dict(item) for item in self.actions],
            "warnings": [dict(item) for item in self.warnings],
            **dict(self.metadata),
        }


def canonicalize_novel_chinese(text: str) -> CanonicalizationResult:
    original = str(text or "")
    repaired = original
    actions: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    for source, target in _LITERAL_REPLACEMENTS:
        count = repaired.count(source)
        if count:
            repaired = repaired.replace(source, target)
            actions.append({"type": "literal_collocation", "from": source, "to": target, "count": count})

    # Deterministic punctuation/spacing cleanup only.
    normalized = re.sub(r"([，。！？；：、])\1+", r"\1", repaired)
    if normalized != repaired:
        repaired = normalized
        actions.append({"type": "collapse_duplicate_cjk_punctuation"})

    # Diagnose but do not rewrite phrases whose intended action is ambiguous.
    for phrase, code in (
        ("嘔了一口氣", "AMBIGUOUS_BREATH_COLLOCATION"),
        ("被濃厚的青綠色海水", "AWKWARD_COLOR_COLLOCATION"),
    ):
        if phrase in repaired:
            warnings.append({"code": code, "phrase": phrase, "auto_repaired": False})

    return CanonicalizationResult(
        text=repaired,
        changed=repaired != original,
        actions=tuple(actions),
        warnings=tuple(warnings),
        metadata={
            "semantic_rewrite_allowed": False,
            "provider_called": False,
            "fail_closed": True,
        },
    )
