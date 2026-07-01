from __future__ import annotations

from typing import Any, Dict
import time


def create_executor_metrics() -> Dict[str, Any]:
    return {
        "started_at": time.time(),
        "completed_at": None,
        "total": 0,
        "completed": 0,
        "failed": 0,
        "attempts": 0,
        "duration_ms": 0,
    }


def record_executor_result(metrics: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    metrics["total"] = metrics.get("total", 0) + 1
    metrics["attempts"] = metrics.get("attempts", 0) + int(result.get("attempts", 0))
    if result.get("status") == "completed":
        metrics["completed"] = metrics.get("completed", 0) + 1
    elif result.get("status") == "failed":
        metrics["failed"] = metrics.get("failed", 0) + 1
    metrics["completed_at"] = time.time()
    metrics["duration_ms"] = int((metrics["completed_at"] - metrics.get("started_at", metrics["completed_at"])) * 1000)
    return metrics


def executor_metrics_manifest(metrics: Dict[str, Any]) -> Dict[str, Any]:
    total = metrics.get("total", 0)
    return {
        "kind": "ntpe.executor.metrics",
        "version": "06.5",
        "total": total,
        "completed": metrics.get("completed", 0),
        "failed": metrics.get("failed", 0),
        "attempts": metrics.get("attempts", 0),
        "success_rate": 1.0 if total == 0 else metrics.get("completed", 0) / total,
        "duration_ms": metrics.get("duration_ms", 0),
    }
