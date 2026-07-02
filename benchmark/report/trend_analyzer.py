from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping


class TrendAnalyzer:
    def analyze(self, reports: Iterable[Mapping[str, Any]], metric: str = "elapsed_ms") -> Dict[str, Any]:
        values: List[float] = []
        for report in reports:
            values.append(float((report.get("summary") or {}).get(metric, 0.0) or 0.0))
        if not values:
            direction = "flat"
        elif len(values) == 1:
            direction = "flat"
        elif values[-1] > values[0]:
            direction = "up"
        elif values[-1] < values[0]:
            direction = "down"
        else:
            direction = "flat"
        return {
            "schema": "ntpe.performance.trend.v1",
            "metric": metric,
            "count": len(values),
            "values": values,
            "min": min(values) if values else 0.0,
            "max": max(values) if values else 0.0,
            "average": (sum(values) / len(values)) if values else 0.0,
            "direction": direction,
        }


def analyze_trends(reports: Iterable[Mapping[str, Any]], metric: str = "elapsed_ms") -> Dict[str, Any]:
    return TrendAnalyzer().analyze(reports, metric)
