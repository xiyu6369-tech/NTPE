# =====================================================
# NTPE 1.2 Professional
# Stage-16.6 Adaptive Translation Strategy
# =====================================================

from __future__ import annotations

import re
from typing import List, Tuple

from .adaptive_strategy_context import AdaptiveStrategyContext
from .adaptive_strategy_policy import AdaptiveStrategyPolicy
from .adaptive_strategy_result import AdaptiveStrategyCandidate


def classify_content(text: str, hint: str | None = None) -> str:
    if hint:
        return hint
    stripped = text.strip()
    if not stripped:
        return "general"
    dialogue_marks = stripped.count("「") + stripped.count("」") + stripped.count('"')
    lines = [line for line in stripped.splitlines() if line.strip()]
    bullets = sum(1 for line in lines if re.match(r"^\s*([-*•]|\d+[.)])\s+", line))
    technical_terms = len(re.findall(r"\b(API|JSON|HTTP|Python|class|function|token|config|schema)\b", stripped, re.I))
    if technical_terms >= 2 or bullets >= max(2, len(lines) // 2 if lines else 2):
        return "technical"
    if dialogue_marks >= 2 or re.search(r"[說問答道]\s*[：:]", stripped):
        return "dialogue"
    if len(stripped) > 120 or re.search(r"他|她|男人|女人|房間|門|視線|沉默", stripped):
        return "novel"
    return "general"


class AdaptiveStrategySelector:
    def __init__(self, policy: AdaptiveStrategyPolicy | None = None) -> None:
        self.policy = policy or AdaptiveStrategyPolicy()

    def score(self, context: AdaptiveStrategyContext) -> Tuple[str, List[AdaptiveStrategyCandidate]]:
        content_type = classify_content(context.source_text, context.content_type_hint)
        candidates: List[AdaptiveStrategyCandidate] = []
        for profile in self.policy.get_profiles():
            score = 0.0
            reasons: List[str] = []
            if content_type in profile.content_types:
                score += 0.45
                reasons.append(f"content_type:{content_type}")
            elif "mixed" in profile.content_types and content_type in {"general", "novel", "dialogue"}:
                score += 0.2
                reasons.append("mixed_content_compatible")
            if context.quality_risks:
                score += profile.priority("fidelity") * 0.15
                reasons.append("quality_risk")
            if context.narrative_signals:
                score += profile.priority("narrative") * 0.12
                reasons.append("narrative_signal")
            if context.character_signals:
                score += profile.priority("character") * 0.12
                reasons.append("character_signal")
            if context.memory_signals:
                score += profile.priority("terminology") * 0.08
                reasons.append("memory_signal")
            if context.provider_capabilities.get("low_latency"):
                score += profile.priority("speed") * 0.05
                reasons.append("provider_low_latency")
            if self.policy.prefer_quality_over_speed:
                score += (profile.priority("fidelity") + profile.priority("fluency")) * 0.04
                reasons.append("quality_preferred")
            candidates.append(AdaptiveStrategyCandidate(profile=profile, score=round(min(score, 1.0), 4), reasons=reasons))
        candidates.sort(key=lambda item: item.score, reverse=True)
        return content_type, candidates
