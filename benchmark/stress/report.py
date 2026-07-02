from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable

from benchmark.benchmark_result import BenchmarkResult


def build_stress_report(results: Iterable[BenchmarkResult]) -> Dict[str, Any]:
    items = [result.to_dict() for result in results]
    return {
        "type": "stress_soak_report",
        "status": "PASS" if all(item.get("status") == "PASS" for item in items) else "FAIL",
        "count": len(items),
        "results": items,
    }


def write_stress_report(results: Iterable[BenchmarkResult], path: str | Path) -> Dict[str, Any]:
    report = build_stress_report(results)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
