from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable

from .benchmark_result import BenchmarkResult


class JSONBenchmarkReportWriter:
    def write(self, results: Iterable[BenchmarkResult], path: str | Path, metadata: Dict[str, Any] | None = None) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        result_list = list(results)
        payload = {
            "schema": "ntpe.benchmark.report.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
            "summary": {
                "total": len(result_list),
                "passed": sum(1 for r in result_list if r.is_passed()),
                "failed": sum(1 for r in result_list if not r.is_passed()),
            },
            "results": [r.to_dict() for r in result_list],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
