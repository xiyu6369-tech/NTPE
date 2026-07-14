from __future__ import annotations

SEVERITIES = ("info", "low", "medium", "high", "critical")
SEVERITY_RANK = {value: index for index, value in enumerate(SEVERITIES)}


def validate_severity(value: str) -> str:
    if value not in SEVERITY_RANK:
        raise ValueError(f"unsupported defect severity: {value}")
    return value


def severity_rank(value: str) -> int:
    validate_severity(value)
    return SEVERITY_RANK[value]
