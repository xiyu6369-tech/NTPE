from __future__ import annotations

QUALITY_DIMENSIONS = (
    "naturalness", "fidelity", "completeness", "narrative", "dialogue",
    "terminology", "consistency", "traditional_chinese_style", "readability", "overall",
)
QUALITY_DIMENSION_SET = frozenset(QUALITY_DIMENSIONS)


def validate_dimension(value: str) -> str:
    if value not in QUALITY_DIMENSION_SET:
        raise ValueError(f"unsupported quality dimension: {value}")
    return value
