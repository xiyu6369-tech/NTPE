from __future__ import annotations


def coverage_ratio(source_count: int, translated_count: int) -> float:
    if source_count <= 0:
        return 1.0
    return max(0.0, min(1.0, translated_count / source_count))


def evidence_reliability(*, confidence: float, has_source_range: bool, has_translated_range: bool = False, translated_range_required: bool = False) -> bool:
    if confidence < 0.70 or not has_source_range:
        return False
    return has_translated_range if translated_range_required else True
