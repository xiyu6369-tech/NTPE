from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from uuid import uuid4
from typing import Any

from .job import utc_now


DEFAULT_THRESHOLDS = {
    "elapsed_seconds_warn_ratio": 1.25,
    "elapsed_seconds_fail_ratio": 1.50,
    "avg_job_seconds_warn_ratio": 1.25,
    "avg_job_seconds_fail_ratio": 1.50,
    "retry_attempts_warn_delta": 2,
    "retry_attempts_fail_delta": 5,
    "failed_warn_delta": 1,
    "failed_fail_delta": 2,
}


class PerformanceRegressionChecker:
    def create_snapshot(self, report: dict[str, Any], stage: str | None = None, source: str | None = None) -> dict[str, Any]:
        return {
            "snapshot_id": str(uuid4()),
            "stage": stage,
            "created_at": utc_now().isoformat(),
            "scheduler": deepcopy(report.get("scheduler", {})),
            "queue": deepcopy(report.get("queue", {})),
            "retry": deepcopy(report.get("retry", {})),
            "collector": deepcopy(report.get("collector", {})),
            "performance": deepcopy(report.get("performance", {})),
            "journal": deepcopy(report.get("journal", {})),
            "source": source,
        }

    def save_snapshot(self, snapshot: dict[str, Any], path: str | Path) -> dict[str, Any]:
        snapshot_path = Path(path)
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        return snapshot

    def load_snapshot(self, path: str | Path) -> dict[str, Any]:
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def compare(
        self,
        baseline: dict[str, Any],
        current: dict[str, Any],
        thresholds: dict[str, float | int] | None = None,
    ) -> dict[str, Any]:
        effective = dict(DEFAULT_THRESHOLDS)
        if thresholds:
            effective.update(thresholds)
        checks = [
            self._ratio_check(
                "elapsed_seconds",
                baseline.get("scheduler", {}).get("elapsed_seconds"),
                current.get("scheduler", {}).get("elapsed_seconds"),
                effective["elapsed_seconds_warn_ratio"],
                effective["elapsed_seconds_fail_ratio"],
            ),
            self._ratio_check(
                "avg_job_seconds",
                baseline.get("performance", {}).get("avg_job_seconds"),
                current.get("performance", {}).get("avg_job_seconds"),
                effective["avg_job_seconds_warn_ratio"],
                effective["avg_job_seconds_fail_ratio"],
            ),
            self._delta_check(
                "retry_attempts",
                baseline.get("retry", {}).get("retry_attempts_total"),
                current.get("retry", {}).get("retry_attempts_total"),
                effective["retry_attempts_warn_delta"],
                effective["retry_attempts_fail_delta"],
            ),
            self._delta_check(
                "failed",
                baseline.get("scheduler", {}).get("failed"),
                current.get("scheduler", {}).get("failed"),
                effective["failed_warn_delta"],
                effective["failed_fail_delta"],
            ),
        ]
        checks = [check for check in checks if check is not None]
        status = self._overall_status(checks)
        return {
            "status": status,
            "baseline_stage": baseline.get("stage"),
            "current_stage": current.get("stage"),
            "checks": checks,
            "regressions": [check for check in checks if check["status"] in {"WARN", "FAIL"}],
            "improvements": [check for check in checks if check["status"] == "IMPROVED"],
            "summary": {
                "checks_total": len(checks),
                "warn": sum(1 for check in checks if check["status"] == "WARN"),
                "fail": sum(1 for check in checks if check["status"] == "FAIL"),
                "improved": sum(1 for check in checks if check["status"] == "IMPROVED"),
            },
            "created_at": utc_now().isoformat(),
        }

    def append_history(self, comparison: dict[str, Any], path: str | Path) -> list[dict[str, Any]]:
        history_path = Path(path)
        history_path.parent.mkdir(parents=True, exist_ok=True)
        history = self.load_history(history_path) if history_path.exists() else []
        history.append(comparison)
        history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
        return history

    def load_history(self, path: str | Path) -> list[dict[str, Any]]:
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def render_text(self, comparison: dict[str, Any]) -> str:
        lines = [
            "# NTPE Performance Regression",
            "",
            f"{'Baseline Stage':18}{comparison.get('baseline_stage')}",
            f"{'Current Stage':18}{comparison.get('current_stage')}",
            f"{'Status':18}{comparison.get('status')}",
            "",
        ]
        for check in comparison.get("checks", []):
            lines.append(f"{check['metric']:18}{check['baseline']} -> {check['current']}  {check['status']}")
        return "\n".join(lines)

    def render_json(self, comparison: dict[str, Any]) -> str:
        return json.dumps(comparison, ensure_ascii=False, indent=2)

    def _ratio_check(
        self,
        metric: str,
        baseline: float | int | None,
        current: float | int | None,
        warn_ratio: float,
        fail_ratio: float,
    ) -> dict[str, Any] | None:
        if baseline is None or current is None:
            return None
        ratio = None if baseline == 0 else current / baseline
        if current < baseline:
            status = "IMPROVED"
        elif ratio is not None and ratio >= fail_ratio:
            status = "FAIL"
        elif ratio is not None and ratio >= warn_ratio:
            status = "WARN"
        else:
            status = "PASS"
        return {
            "metric": metric,
            "baseline": baseline,
            "current": current,
            "ratio": ratio,
            "status": status,
            "threshold": f"warn_ratio={warn_ratio:.2f} fail_ratio={fail_ratio:.2f}",
        }

    def _delta_check(
        self,
        metric: str,
        baseline: float | int | None,
        current: float | int | None,
        warn_delta: float | int,
        fail_delta: float | int,
    ) -> dict[str, Any] | None:
        if baseline is None or current is None:
            return None
        delta = current - baseline
        if delta < 0:
            status = "IMPROVED"
        elif delta >= fail_delta:
            status = "FAIL"
        elif delta >= warn_delta:
            status = "WARN"
        else:
            status = "PASS"
        return {
            "metric": metric,
            "baseline": baseline,
            "current": current,
            "delta": delta,
            "status": status,
            "threshold": f"warn_delta={warn_delta} fail_delta={fail_delta}",
        }

    def _overall_status(self, checks: list[dict[str, Any]]) -> str:
        if any(check["status"] == "FAIL" for check in checks):
            return "FAIL"
        if any(check["status"] == "WARN" for check in checks):
            return "WARN"
        return "PASS"
