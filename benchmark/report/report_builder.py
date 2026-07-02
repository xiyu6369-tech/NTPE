from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping

try:
    from benchmark.benchmark_result import BenchmarkResult
except Exception:  # pragma: no cover
    BenchmarkResult = Any  # type: ignore


def _result_to_dict(result: Any) -> Dict[str, Any]:
    if hasattr(result, "to_dict"):
        return dict(result.to_dict())
    if isinstance(result, Mapping):
        return dict(result)
    return {"name": str(result), "status": "PASS", "metrics": {}}


def _category_of(item: Mapping[str, Any]) -> str:
    metrics = item.get("metrics") or {}
    if "category" in metrics:
        return str(metrics["category"])
    name = str(item.get("name", "benchmark"))
    for prefix in ("runtime", "provider", "stress", "soak", "cache", "knowledge", "translation"):
        if name.lower().startswith(prefix):
            return prefix
    return "general"


@dataclass
class PerformanceReportBuilder:
    metadata: Dict[str, Any] = field(default_factory=dict)

    def build(self, results: Iterable[Any], *, title: str = "NTPE Performance Report") -> Dict[str, Any]:
        items = [_result_to_dict(r) for r in results]
        total = len(items)
        passed = sum(1 for r in items if str(r.get("status", "PASS")) == "PASS")
        failed = total - passed
        elapsed = sum(float(r.get("elapsed_ms", 0.0) or 0.0) for r in items)
        peak_memory = max([int(r.get("peak_memory_bytes", 0) or 0) for r in items] or [0])
        by_category: Dict[str, Dict[str, Any]] = {}
        for item in items:
            category = _category_of(item)
            bucket = by_category.setdefault(category, {"count": 0, "passed": 0, "failed": 0, "elapsed_ms": 0.0})
            bucket["count"] += 1
            if str(item.get("status", "PASS")) == "PASS":
                bucket["passed"] += 1
            else:
                bucket["failed"] += 1
            bucket["elapsed_ms"] += float(item.get("elapsed_ms", 0.0) or 0.0)
        return {
            "schema": "ntpe.performance.report.v1",
            "title": title,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": dict(self.metadata),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "status": "PASS" if failed == 0 else "FAIL",
                "elapsed_ms": round(elapsed, 6),
                "peak_memory_bytes": peak_memory,
            },
            "categories": by_category,
            "results": items,
        }


def build_performance_report(results: Iterable[Any], metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return PerformanceReportBuilder(metadata=metadata or {}).build(results)
