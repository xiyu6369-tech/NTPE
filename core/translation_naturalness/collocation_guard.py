from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

LITERARY_COLLOCATION_GUARD_VERSION = "6.0.0-stage12.3"

# Deterministic replacements only. These expressions have a stable, non-semantic
# correction and do not require guessing the source action or narrative intent.
_SAFE_REPLACEMENTS: tuple[tuple[str, str, str], ...] = (
    ("若要是觸怒了他", "要是惹怒了他", "redundant_conditional_collocation"),
    ("若要是惹怒了他", "要是惹怒了他", "redundant_conditional_collocation"),
    ("和他纏繞在一起", "和他糾纏", "awkward_interaction_collocation"),
    ("和他纏繞", "和他糾纏", "awkward_interaction_collocation"),
    ("用著冷漠的眼神", "用冷漠的眼神", "redundant_aspect_particle"),
    ("涼涼的風吹過來", "一陣涼風吹過", "awkward_weather_collocation"),
)

# These phrases are suspicious, but the intended action/meaning cannot be
# recovered safely without source-level semantic evidence. They are warnings.
_WARNING_PHRASES: tuple[tuple[str, str, str], ...] = (
    ("嘔了一口氣", "AMBIGUOUS_BREATH_ACTION", "動作搭配不自然，需比對原文判定是吐氣、倒吸氣或嘆氣。"),
    ("被濃厚的青綠色海水", "AWKWARD_COLOR_COLLOCATION", "顏色與質感修飾搭配生硬，但不宜在無原文證據時自動改寫。"),
    ("秘書般的人", "AWKWARD_ROLE_COLLOCATION", "人物身分描寫偏直譯，若 canonicalizer 未處理則保留警告。"),
)


@dataclass(frozen=True)
class LiteraryCollocationResult:
    text: str
    changed: bool
    actions: tuple[dict[str, Any], ...] = ()
    warnings: tuple[dict[str, Any], ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "version": LITERARY_COLLOCATION_GUARD_VERSION,
            "changed": self.changed,
            "actions": [dict(item) for item in self.actions],
            "warnings": [dict(item) for item in self.warnings],
            "semantic_rewrite_allowed": False,
            "provider_called": False,
            "fail_closed": True,
            **dict(self.metadata),
        }


def apply_literary_collocation_guard(text: str) -> LiteraryCollocationResult:
    original = str(text or "")
    repaired = original
    actions: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    for source, target, rule_code in _SAFE_REPLACEMENTS:
        count = repaired.count(source)
        if count:
            repaired = repaired.replace(source, target)
            actions.append({
                "type": "safe_collocation_repair",
                "rule_code": rule_code,
                "from": source,
                "to": target,
                "count": count,
            })

    for phrase, code, message in _WARNING_PHRASES:
        if phrase in repaired:
            warnings.append({
                "code": code,
                "phrase": phrase,
                "message": message,
                "auto_repaired": False,
            })

    return LiteraryCollocationResult(
        text=repaired,
        changed=repaired != original,
        actions=tuple(actions),
        warnings=tuple(warnings),
        metadata={"safe_replacement_count": len(actions)},
    )
