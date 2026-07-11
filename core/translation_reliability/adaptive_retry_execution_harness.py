
from __future__ import annotations

from typing import Any, Callable, Dict, List, Mapping, Optional

from .adaptive_retry_policy import AdaptiveRetryPolicy
from .adaptive_chunk_split_planner import AdaptiveChunkSplitPlanner


Handler = Callable[[str, Mapping[str, Any]], Mapping[str, Any]]
RebuildCallback = Callable[[], Any]
SleepCallback = Callable[[int], Any]


class AdaptiveRetryExecutionHarness:
    """Execute bounded retry recovery through injected callbacks only.

    The harness is disabled by default and does not import Provider Runtime,
    Translation Runtime, HTTP clients, API keys, or launcher code.

    A caller may inject a handler for isolated validation. The harness records
    decisions and attempts without persisting source or translated text.
    """

    version = "TE-v4.1"
    stage = "4.1.1"
    name = "adaptive_retry_execution_harness"

    def __init__(self) -> None:
        self.retry_policy = AdaptiveRetryPolicy()
        self.split_planner = AdaptiveChunkSplitPlanner()

    def execute(
        self,
        source_text: Optional[str],
        handler: Optional[Handler],
        config: Optional[Mapping[str, Any]] = None,
        rebuild_callback: Optional[RebuildCallback] = None,
        sleep_callback: Optional[SleepCallback] = None,
    ) -> Dict[str, Any]:
        cfg = self._normalize_config(config)

        if not cfg["enabled"]:
            return self._disabled_result()

        if handler is None or not callable(handler):
            return self._failure_result(
                status="invalid_handler",
                reason="handler_required",
                attempts=[],
                rebuild_count=0,
                split_count=0,
            )

        source = str(source_text or "")
        if not source:
            return self._failure_result(
                status="invalid_source",
                reason="source_text_required",
                attempts=[],
                rebuild_count=0,
                split_count=0,
            )

        attempts: List[Dict[str, Any]] = []
        rebuild_count = 0
        split_count = 0
        current_texts = [source]
        current_timeout = cfg["timeout_seconds"]
        current_chunk_size = min(len(source), cfg["chunk_size"])
        last_outcome = "unknown_failure"

        for attempt_index in range(1, cfg["max_attempts"] + 1):
            segment_results = []
            aggregate_success = True
            aggregate_outcome = "success"

            for segment_index, segment_text in enumerate(current_texts, start=1):
                raw = dict(handler(
                    segment_text,
                    {
                        "attempt": attempt_index,
                        "segment_index": segment_index,
                        "segment_count": len(current_texts),
                        "timeout_seconds": current_timeout,
                        "chunk_size": current_chunk_size,
                    },
                ) or {})

                outcome = str(raw.get("outcome") or "unknown_failure")
                success = outcome == "success" and bool(raw.get("translated_text", ""))
                segment_results.append({
                    "segment_index": segment_index,
                    "outcome": outcome,
                    "success": success,
                    "translated_chars": len(str(raw.get("translated_text") or "")),
                    "provider_attempts": max(0, int(raw.get("provider_attempts", 0) or 0)),
                    "latency_ms": max(0, int(raw.get("latency_ms", 0) or 0)),
                })

                if not success:
                    aggregate_success = False
                    aggregate_outcome = outcome
                    break

            attempts.append({
                "attempt": attempt_index,
                "segment_count": len(current_texts),
                "timeout_seconds": current_timeout,
                "chunk_size": current_chunk_size,
                "outcome": "success" if aggregate_success else aggregate_outcome,
                "success": aggregate_success,
                "segments": segment_results,
            })

            if aggregate_success:
                return {
                    "status": "completed",
                    "success": True,
                    "stage": self.stage,
                    "attempts_used": attempt_index,
                    "rebuild_count": rebuild_count,
                    "split_count": split_count,
                    "attempts": attempts,
                    "final_outcome": "success",
                    "execution_mode": "isolated_callback",
                    "source_text_retained": False,
                    "translated_text_retained": False,
                    "integration_status": self._integration_status(
                        retry_executed=attempt_index > 1,
                        split_executed=split_count > 0,
                        rebuild_executed=rebuild_count > 0,
                    ),
                    "metadata": self._metadata(),
                }

            last_outcome = aggregate_outcome
            decision = self.retry_policy.decide(
                {
                    "outcome": aggregate_outcome,
                    "attempt": attempt_index,
                    "max_attempts": cfg["max_attempts"],
                    "timeout_seconds": current_timeout,
                    "chunk_size": current_chunk_size,
                },
                {
                    "max_attempts": cfg["max_attempts"],
                    "base_delay_seconds": cfg["base_delay_seconds"],
                    "max_delay_seconds": cfg["max_delay_seconds"],
                    "base_timeout_seconds": cfg["timeout_seconds"],
                    "max_timeout_seconds": cfg["max_timeout_seconds"],
                    "base_chunk_size": cfg["chunk_size"],
                    "min_chunk_size": cfg["min_chunk_size"],
                    "allow_provider_switch": False,
                },
            )

            attempts[-1]["decision"] = {
                key: value
                for key, value in decision.items()
                if key != "metadata"
            }

            if decision["retry"] is not True:
                break

            if decision["rebuild_provider_session"] is True and callable(rebuild_callback):
                rebuild_callback()
                rebuild_count += 1

            if decision["delay_seconds"] > 0 and callable(sleep_callback):
                sleep_callback(int(decision["delay_seconds"]))

            current_timeout = int(decision["next_timeout_seconds"])
            current_chunk_size = int(decision["next_chunk_size"])

            plan = self.split_planner.plan(
                source,
                decision,
                {
                    "min_chunk_size": cfg["min_chunk_size"],
                    "default_chunk_size": cfg["chunk_size"],
                    "max_chunk_size": cfg["max_chunk_size"],
                    "overlap_chars": 0,
                },
            )
            if plan["should_split"] is True:
                current_texts = [
                    str(segment["text"])
                    for segment in plan["segments"]
                ]
                split_count += 1
            else:
                current_texts = [source]

        return self._failure_result(
            status="failed",
            reason="recovery_exhausted",
            attempts=attempts,
            rebuild_count=rebuild_count,
            split_count=split_count,
            final_outcome=last_outcome,
        )

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False

        required = {
            "status",
            "success",
            "stage",
            "attempts_used",
            "rebuild_count",
            "split_count",
            "attempts",
            "final_outcome",
            "execution_mode",
            "source_text_retained",
            "translated_text_retained",
            "integration_status",
            "metadata",
        }
        if not required.issubset(result):
            return False
        if result.get("stage") != self.stage:
            return False
        if result.get("source_text_retained") is not False:
            return False
        if result.get("translated_text_retained") is not False:
            return False

        integration = result.get("integration_status")
        if not isinstance(integration, Mapping):
            return False

        for key in (
            "provider_runtime_modified",
            "translation_runtime_modified",
            "launcher_modified",
            "http_client_imported",
            "api_key_accessed",
            "real_translation_runtime_used",
        ):
            if integration.get(key) is not False:
                return False

        if result.get("status") == "disabled":
            return result.get("success") is False and result.get("attempts") == []

        if result.get("status") == "completed":
            return result.get("success") is True and result.get("final_outcome") == "success"

        return result.get("success") is False

    def _disabled_result(self) -> Dict[str, Any]:
        return {
            "status": "disabled",
            "success": False,
            "stage": self.stage,
            "attempts_used": 0,
            "rebuild_count": 0,
            "split_count": 0,
            "attempts": [],
            "final_outcome": "not_started",
            "execution_mode": "disabled",
            "source_text_retained": False,
            "translated_text_retained": False,
            "integration_status": self._integration_status(),
            "metadata": self._metadata(),
        }

    def _failure_result(
        self,
        *,
        status: str,
        reason: str,
        attempts: List[Dict[str, Any]],
        rebuild_count: int,
        split_count: int,
        final_outcome: str = "not_started",
    ) -> Dict[str, Any]:
        return {
            "status": status,
            "success": False,
            "stage": self.stage,
            "reason": reason,
            "attempts_used": len(attempts),
            "rebuild_count": rebuild_count,
            "split_count": split_count,
            "attempts": attempts,
            "final_outcome": final_outcome,
            "execution_mode": "isolated_callback",
            "source_text_retained": False,
            "translated_text_retained": False,
            "integration_status": self._integration_status(
                retry_executed=len(attempts) > 1,
                split_executed=split_count > 0,
                rebuild_executed=rebuild_count > 0,
            ),
            "metadata": self._metadata(),
        }

    @staticmethod
    def _normalize_config(config: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
        src = dict(config or {})
        return {
            "enabled": src.get("enabled") is True,
            "max_attempts": max(1, int(src.get("max_attempts", 5) or 5)),
            "base_delay_seconds": max(0, int(src.get("base_delay_seconds", 5) or 5)),
            "max_delay_seconds": max(1, int(src.get("max_delay_seconds", 60) or 60)),
            "timeout_seconds": max(1, int(src.get("timeout_seconds", 180) or 180)),
            "max_timeout_seconds": max(1, int(src.get("max_timeout_seconds", 300) or 300)),
            "chunk_size": max(1, int(src.get("chunk_size", 600) or 600)),
            "min_chunk_size": max(1, int(src.get("min_chunk_size", 200) or 200)),
            "max_chunk_size": max(1, int(src.get("max_chunk_size", 1200) or 1200)),
        }

    @staticmethod
    def _integration_status(
        *,
        retry_executed: bool = False,
        split_executed: bool = False,
        rebuild_executed: bool = False,
    ) -> Dict[str, Any]:
        return {
            "mode": "isolated_callback",
            "retry_executed": retry_executed,
            "split_executed": split_executed,
            "rebuild_callback_executed": rebuild_executed,
            "provider_runtime_modified": False,
            "translation_runtime_modified": False,
            "launcher_modified": False,
            "http_client_imported": False,
            "api_key_accessed": False,
            "real_translation_runtime_used": False,
        }

    def _metadata(self) -> Dict[str, Any]:
        return {
            "harness": self.name,
            "version": self.version,
            "stage": self.stage,
            "handler_injected": True,
            "provider_imported": False,
            "runtime_imported": False,
        }


__all__ = ["AdaptiveRetryExecutionHarness"]
