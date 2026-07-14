from __future__ import annotations

from core.translation_quality_defects import TranslationDefect

SEVERITY_PENALTIES = {"info": 1.0, "low": 5.0, "medium": 12.0, "high": 25.0, "critical": 45.0}


def score_evidence(defects: tuple[TranslationDefect, ...]) -> float:
    penalty = sum(SEVERITY_PENALTIES[row.severity] for row in defects)
    penalty += 10.0 * sum(1 for row in defects if row.blocking)
    return round(max(0.0, 100.0 - penalty), 2)
