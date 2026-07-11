
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional

from .adaptive_retry_policy import AdaptiveRetryPolicy
from .adaptive_chunk_split_planner import AdaptiveChunkSplitPlanner


class RetryStrategyBenchmark:
    """Compare fixed retry and adaptive retry strategies with supplied cases.

    This benchmark is deterministic and side-effect free. It does not execute
    retries, sleep, call providers, access HTTP, or modify Translation Runtime.
    """

    version = "TE-v4.0"
    stage = "4.0.5"
    name = "retry_strategy_benchmark"

    def __init__(self) -> None:
        self.retry_policy = AdaptiveRetryPolicy()
        self.split_planner = AdaptiveChunkSplitPlanner()

    def run(
        self,
        cases: Iterable[Mapping[str, Any]],
        fixed_policy: Optional[Mapping[str, Any]] = None,
        adaptive_policy: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        case_list = [dict(case) for case in cases]
        fixed_cfg = self._fixed_config(fixed_policy)
        adaptive_cfg = dict(adaptive_policy or {})

        fixed_results = [self._simulate_fixed(case, fixed_cfg) for case in case_list]
        adaptive_results = [
            self._simulate_adaptive(case, adaptive_cfg) for case in case_list
        ]

        fixed_summary = self._summarize(fixed_results)
        adaptive_summary = self._summarize(adaptive_results)

        comparison = {
            "success_rate_gain": round(
                adaptive_summary["success_rate"] - fixed_summary["success_rate"], 2
            ),
            "retry_reduction": fixed_summary["total_retries"] - adaptive_summary["total_retries"],
            "estimated_time_reduction_ms": (
                fixed_summary["estimated_total_time_ms"]
                - adaptive_summary["estimated_total_time_ms"]
            ),
            "split_recoveries": adaptive_summary["split_recoveries"],
            "provider_rebuild_recoveries": adaptive_summary["provider_rebuild_recoveries"],
            "adaptive_better": self._is_adaptive_better(
                fixed_summary, adaptive_summary
            ),
        }

        return {
            "version": self.version,
            "stage": self.stage,
            "benchmark": self.name,
            "cases_total": len(case_list),
            "fixed_strategy": {
                "config": fixed_cfg,
                "summary": fixed_summary,
                "results": fixed_results,
            },
            "adaptive_strategy": {
                "config": adaptive_cfg,
                "summary": adaptive_summary,
                "results": adaptive_results,
            },
            "comparison": comparison,
            "recommendation": (
                "adopt_adaptive_retry_and_chunk_split"
                if comparison["adaptive_better"]
                else "keep_current_strategy_and_collect_more_data"
            ),
            "safety": {
                "provider_called": False,
                "http_called": False,
                "api_key_accessed": False,
                "sleep_executed": False,
                "runtime_modified": False,
                "launcher_modified": False,
                "real_translation_executed": False,
            },
        }

    def validate_report(self, report: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(report, Mapping):
            return False
        required = {
            "version",
            "stage",
            "benchmark",
            "cases_total",
            "fixed_strategy",
            "adaptive_strategy",
            "comparison",
            "recommendation",
            "safety",
        }
        if not required.issubset(report):
            return False
        if report.get("version") != self.version or report.get("stage") != self.stage:
            return False

        for key in ("fixed_strategy", "adaptive_strategy"):
            strategy = report.get(key)
            if not isinstance(strategy, Mapping):
                return False
            summary = strategy.get("summary")
            results = strategy.get("results")
            if not isinstance(summary, Mapping) or not isinstance(results, list):
                return False
            if len(results) != int(report.get("cases_total", -1)):
                return False

        safety = report.get("safety")
        if not isinstance(safety, Mapping):
            return False
        for key in (
            "provider_called",
            "http_called",
            "api_key_accessed",
            "sleep_executed",
            "runtime_modified",
            "launcher_modified",
            "real_translation_executed",
        ):
            if safety.get(key) is not False:
                return False
        return True

    def _simulate_fixed(
        self,
        case: Mapping[str, Any],
        cfg: Mapping[str, Any],
    ) -> Dict[str, Any]:
        outcome = str(case.get("outcome") or "unknown_failure")
        attempts_needed = max(1, int(case.get("attempts_needed", 1) or 1))
        max_attempts = int(cfg["max_attempts"])
        latency_ms = max(0, int(case.get("latency_ms", 0) or 0))
        delay_ms = int(cfg["delay_seconds"]) * 1000
        recoverable = bool(case.get("fixed_recoverable", outcome == "success"))

        success = outcome == "success" or (recoverable and attempts_needed <= max_attempts)
        attempts_used = min(attempts_needed, max_attempts)
        retries = max(0, attempts_used - 1)
        estimated_time = attempts_used * latency_ms + retries * delay_ms

        return {
            "case_id": str(case.get("case_id") or ""),
            "strategy": "fixed",
            "outcome": outcome,
            "success": success,
            "attempts_used": attempts_used,
            "retries": retries,
            "estimated_time_ms": estimated_time,
            "chunk_split": False,
            "provider_rebuild": False,
            "final_reason": "fixed_retry_success" if success else "fixed_retry_failed",
        }

    def _simulate_adaptive(
        self,
        case: Mapping[str, Any],
        cfg: Mapping[str, Any],
    ) -> Dict[str, Any]:
        outcome = str(case.get("outcome") or "unknown_failure")
        latency_ms = max(0, int(case.get("latency_ms", 0) or 0))
        attempt = max(0, int(case.get("attempt", 0) or 0))
        max_attempts = max(1, int(case.get("max_attempts", 5) or 5))
        chunk_size = max(1, int(case.get("chunk_size", 600) or 600))
        timeout_seconds = max(1, int(case.get("timeout_seconds", 180) or 180))

        decision = self.retry_policy.decide(
            {
                "outcome": outcome,
                "attempt": attempt,
                "max_attempts": max_attempts,
                "chunk_size": chunk_size,
                "timeout_seconds": timeout_seconds,
            },
            cfg,
        )

        source_text = str(case.get("source_text") or ("가" * chunk_size))
        split_plan = self.split_planner.plan(source_text, decision)

        adaptive_recoverable = bool(
            case.get(
                "adaptive_recoverable",
                outcome
                in {
                    "success",
                    "http_429",
                    "http_500",
                    "http_503",
                    "read_timeout",
                    "connect_timeout",
                    "connection_error",
                    "ssl_error",
                    "json_decode_error",
                    "provider_not_attempted",
                    "empty_output",
                    "too_short",
                    "hangul_residue",
                    "duplicate_output",
                },
            )
        )

        if outcome == "success":
            success = True
            attempts_used = 1
            retries = 0
        elif decision["retry"] is True and adaptive_recoverable:
            success = True
            attempts_used = 2
            retries = 1
        else:
            success = False
            attempts_used = 1
            retries = 0

        split_factor = split_plan["segment_count"] if split_plan["should_split"] else 1
        retry_latency = max(1, latency_ms // split_factor)
        estimated_time = latency_ms
        if retries:
            estimated_time += decision["delay_seconds"] * 1000
            estimated_time += retry_latency * split_factor

        return {
            "case_id": str(case.get("case_id") or ""),
            "strategy": "adaptive",
            "outcome": outcome,
            "success": success,
            "attempts_used": attempts_used,
            "retries": retries,
            "estimated_time_ms": estimated_time,
            "chunk_split": split_plan["should_split"],
            "split_segments": split_plan["segment_count"],
            "provider_rebuild": decision["rebuild_provider_session"],
            "provider_switch": decision["switch_provider"],
            "next_timeout_seconds": decision["next_timeout_seconds"],
            "next_chunk_size": decision["next_chunk_size"],
            "final_reason": (
                "adaptive_recovery_success"
                if success and outcome != "success"
                else "already_successful"
                if outcome == "success"
                else decision["reason"]
            ),
        }

    @staticmethod
    def _fixed_config(policy: Optional[Mapping[str, Any]]) -> Dict[str, int]:
        src = dict(policy or {})
        return {
            "max_attempts": max(1, int(src.get("max_attempts", 3) or 3)),
            "delay_seconds": max(0, int(src.get("delay_seconds", 5) or 5)),
        }

    @staticmethod
    def _summarize(results: List[Mapping[str, Any]]) -> Dict[str, Any]:
        total = len(results)
        success_count = sum(1 for item in results if item.get("success") is True)
        total_retries = sum(int(item.get("retries", 0) or 0) for item in results)
        estimated_total_time = sum(
            int(item.get("estimated_time_ms", 0) or 0) for item in results
        )
        return {
            "cases_total": total,
            "success_count": success_count,
            "failure_count": total - success_count,
            "success_rate": round((success_count / total) * 100, 2) if total else 0.0,
            "total_retries": total_retries,
            "estimated_total_time_ms": estimated_total_time,
            "split_recoveries": sum(
                1
                for item in results
                if item.get("success") is True and item.get("chunk_split") is True
            ),
            "provider_rebuild_recoveries": sum(
                1
                for item in results
                if item.get("success") is True and item.get("provider_rebuild") is True
            ),
        }

    @staticmethod
    def _is_adaptive_better(
        fixed_summary: Mapping[str, Any],
        adaptive_summary: Mapping[str, Any],
    ) -> bool:
        if adaptive_summary["success_rate"] > fixed_summary["success_rate"]:
            return True
        if adaptive_summary["success_rate"] < fixed_summary["success_rate"]:
            return False
        return (
            adaptive_summary["estimated_total_time_ms"]
            < fixed_summary["estimated_total_time_ms"]
        )


__all__ = ["RetryStrategyBenchmark"]
