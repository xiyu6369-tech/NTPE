from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Callable, Mapping

from .quality_enforcement import QUALITY_ENFORCEMENT_VERSION

LOCAL_REPAIR_FRAMEWORK_VERSION = "6.0.0-stage04"

RepairHandler = Callable[[str], tuple[str, list[dict[str, Any]]]]

_TRADITIONAL_REPLACEMENTS = {
    "一周": "一週",
    "本周": "本週",
    "上周": "上週",
    "下周": "下週",
    "每周": "每週",
    "周末": "週末",
    "雇員": "僱員",
}


def _repair_traditional_orthography(text: str) -> tuple[str, list[dict[str, Any]]]:
    repaired = text
    actions: list[dict[str, Any]] = []
    for source, target in _TRADITIONAL_REPLACEMENTS.items():
        count = repaired.count(source)
        if count:
            repaired = repaired.replace(source, target)
            actions.append({
                "handler": "traditional_orthography",
                "from": source,
                "to": target,
                "count": count,
            })
    return repaired, actions


def _repair_dialogue_quotes(text: str) -> tuple[str, list[dict[str, Any]]]:
    # Only convert clearly balanced curly quote pairs. Do not guess unmatched
    # punctuation because doing so may alter narration or nested quotations.
    open_count = text.count("“")
    close_count = text.count("”")
    if not open_count or open_count != close_count:
        return text, []
    repaired = text.replace("“", "「").replace("”", "」")
    return repaired, [{
        "handler": "balanced_dialogue_quotes",
        "from": "“…”",
        "to": "「…」",
        "count": open_count,
    }]


def _repair_safe_spacing(text: str) -> tuple[str, list[dict[str, Any]]]:
    repaired = text
    actions: list[dict[str, Any]] = []
    collapsed = re.sub(r"[ \t]{2,}", " ", repaired)
    if collapsed != repaired:
        actions.append({"handler": "collapse_horizontal_space"})
        repaired = collapsed
    trimmed = re.sub(r"[ \t]+(?=[，。！？；：、」）])", "", repaired)
    if trimmed != repaired:
        actions.append({"handler": "trim_space_before_cjk_punctuation"})
        repaired = trimmed
    return repaired, actions


_DEFAULT_HANDLERS: dict[str, tuple[RepairHandler, ...]] = {
    "SIMPLIFIED_CHINESE": (_repair_traditional_orthography,),
    "DIALOGUE_QUOTE_FORMAT": (_repair_dialogue_quotes,),
    "FORMATTING": (_repair_safe_spacing,),
}


@dataclass(frozen=True)
class LocalRepairResult:
    text: str
    changed: bool
    attempted_codes: tuple[str, ...] = ()
    repaired_codes: tuple[str, ...] = ()
    unresolved_codes: tuple[str, ...] = ()
    actions: tuple[dict[str, Any], ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "version": LOCAL_REPAIR_FRAMEWORK_VERSION,
            "enabled": True,
            "changed": self.changed,
            "attempted_codes": list(self.attempted_codes),
            "repaired_codes": list(self.repaired_codes),
            "unresolved_codes": list(self.unresolved_codes),
            "actions": [dict(item) for item in self.actions],
            **dict(self.metadata),
        }


class AdaptiveLocalRepairFramework:
    """Deterministic, provider-free local repair registry.

    A handler is registered only when it can repair text without interpreting
    or rewriting narrative meaning. Missing handlers are reported as unresolved
    warnings; they are never converted into subjective rewrites.
    """

    def __init__(self, handlers: Mapping[str, tuple[RepairHandler, ...]] | None = None) -> None:
        self.handlers = dict(handlers or _DEFAULT_HANDLERS)

    @staticmethod
    def _local_codes(unified_report: Mapping[str, Any]) -> list[str]:
        codes: list[str] = []
        for issue in unified_report.get("merged_issues") or []:
            if not isinstance(issue, Mapping):
                continue
            metadata = issue.get("metadata") or {}
            if metadata.get("discipline_route") != "local_repair":
                continue
            code = str(issue.get("code") or issue.get("type") or "").upper()
            if code.startswith("V5_"):
                code = code[3:]
            if code and code not in codes:
                codes.append(code)
        return codes

    def repair(self, text: str, unified_report: Mapping[str, Any]) -> LocalRepairResult:
        local_codes = self._local_codes(unified_report)
        repaired_text = str(text or "")
        actions: list[dict[str, Any]] = []
        repaired_codes: list[str] = []
        unresolved_codes: list[str] = []

        for code in local_codes:
            handlers = self.handlers.get(code, ())
            if not handlers:
                unresolved_codes.append(code)
                continue
            before_code = repaired_text
            for handler in handlers:
                repaired_text, handler_actions = handler(repaired_text)
                for action in handler_actions:
                    actions.append({"issue_code": code, **dict(action)})
            if repaired_text != before_code:
                repaired_codes.append(code)
            else:
                unresolved_codes.append(code)

        return LocalRepairResult(
            text=repaired_text,
            changed=repaired_text != str(text or ""),
            attempted_codes=tuple(local_codes),
            repaired_codes=tuple(repaired_codes),
            unresolved_codes=tuple(unresolved_codes),
            actions=tuple(actions),
            metadata={
                "provider_called": False,
                "semantic_rewrite_allowed": False,
                "quality_enforcement_version": QUALITY_ENFORCEMENT_VERSION,
            },
        )


def apply_adaptive_local_repairs(
    text: str,
    unified_report: Mapping[str, Any],
) -> LocalRepairResult:
    return AdaptiveLocalRepairFramework().repair(text, unified_report)
