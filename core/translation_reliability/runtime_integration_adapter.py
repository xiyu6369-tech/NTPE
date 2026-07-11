
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional

from .baseline import TranslationReliabilityBaseline
from .adaptive_retry_policy import AdaptiveRetryPolicy
from .adaptive_chunk_split_planner import AdaptiveChunkSplitPlanner
from .failure_analyzer import TranslationFailureAnalyzer


class ReliabilityRuntimeIntegrationAdapter:
    """Disabled-by-default bridge from runtime metadata to reliability tools.

    This adapter does not modify Translation Runtime, execute retries, split
    real runtime chunks, call providers, call HTTP, read API keys, or touch
    launcher flow. It only maps supplied runtime metadata into analysis input.
    """

    version = "TE-v4.0"
    stage = "4.0.6"
    name = "reliability_runtime_integration_adapter"

    def __init__(self) -> None:
        self.baseline = TranslationReliabilityBaseline()
        self.retry_policy = AdaptiveRetryPolicy()
        self.split_planner = AdaptiveChunkSplitPlanner()
        self.failure_analyzer = TranslationFailureAnalyzer()

    def process(
        self,
        runtime_events: Optional[Iterable[Mapping[str, Any]]] = None,
        config: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        cfg = self._normalize_config(config)

        if not cfg["enabled"]:
            return self._disabled_result()

        events = [
            self._sanitize_event(event)
            for event in (runtime_events or [])
            if isinstance(event, Mapping)
        ]

        baseline_report = self.baseline.build_report(events)
        failure_analysis = self.failure_analyzer.analyze(baseline_report)

        decisions: List[Dict[str, Any]] = []
        split_plans: List[Dict[str, Any]] = []

        for event in baseline_report["events"]:
            if event["outcome"] == "success":
                continue

            decision = self.retry_policy.decide(
                {
                    "outcome": event["outcome"],
                    "attempt": event["retry_count"],
                    "max_attempts": cfg["max_attempts"],
                    "timeout_seconds": cfg["timeout_seconds"],
                    "chunk_size": event["source_chars"] or cfg["chunk_size"],
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

            plan = self.split_planner.plan(
                "X" * max(0, event["source_chars"]),
                decision,
                {
                    "min_chunk_size": cfg["min_chunk_size"],
                    "default_chunk_size": cfg["chunk_size"],
                    "max_chunk_size": cfg["max_chunk_size"],
                    "overlap_chars": 0,
                },
            )

            decisions.append({
                "chunk_index": event["chunk_index"],
                "outcome": event["outcome"],
                "decision": decision,
            })
            split_plans.append({
                "chunk_index": event["chunk_index"],
                "outcome": event["outcome"],
                "plan": self._strip_segment_text(plan),
            })

        return {
            "status": "analysis_completed",
            "enabled": True,
            "stage": self.stage,
            "baseline_report": baseline_report,
            "failure_analysis": failure_analysis,
            "retry_decisions": decisions,
            "split_plans": split_plans,
            "integration_status": {
                "mode": "analysis_only",
                "runtime_modified": False,
                "provider_called": False,
                "http_called": False,
                "api_key_accessed": False,
                "launcher_modified": False,
                "retry_executed": False,
                "split_executed": False,
                "real_translation_executed": False,
            },
            "metadata": {
                "adapter": self.name,
                "version": self.version,
                "events_received": len(events),
                "source_text_retained": False,
                "translated_text_retained": False,
            },
        }

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False

        required = {
            "status",
            "enabled",
            "stage",
            "baseline_report",
            "failure_analysis",
            "retry_decisions",
            "split_plans",
            "integration_status",
            "metadata",
        }
        if not required.issubset(result):
            return False
        if result.get("stage") != self.stage:
            return False

        integration = result.get("integration_status")
        if not isinstance(integration, Mapping):
            return False

        forbidden_true = (
            "runtime_modified",
            "provider_called",
            "http_called",
            "api_key_accessed",
            "launcher_modified",
            "retry_executed",
            "split_executed",
            "real_translation_executed",
        )
        if any(integration.get(key) is not False for key in forbidden_true):
            return False

        metadata = result.get("metadata")
        if not isinstance(metadata, Mapping):
            return False
        if metadata.get("source_text_retained") is not False:
            return False
        if metadata.get("translated_text_retained") is not False:
            return False

        if result.get("enabled") is False:
            return (
                result.get("status") == "disabled"
                and result.get("baseline_report") == {}
                and result.get("failure_analysis") == {}
                and result.get("retry_decisions") == []
                and result.get("split_plans") == []
            )

        if result.get("status") != "analysis_completed":
            return False
        if not self.baseline.validate_report(result.get("baseline_report")):
            return False
        if not self.failure_analyzer.validate_analysis(result.get("failure_analysis")):
            return False
        return True

    def _disabled_result(self) -> Dict[str, Any]:
        return {
            "status": "disabled",
            "enabled": False,
            "stage": self.stage,
            "baseline_report": {},
            "failure_analysis": {},
            "retry_decisions": [],
            "split_plans": [],
            "integration_status": {
                "mode": "disabled",
                "runtime_modified": False,
                "provider_called": False,
                "http_called": False,
                "api_key_accessed": False,
                "launcher_modified": False,
                "retry_executed": False,
                "split_executed": False,
                "real_translation_executed": False,
            },
            "metadata": {
                "adapter": self.name,
                "version": self.version,
                "events_received": 0,
                "source_text_retained": False,
                "translated_text_retained": False,
            },
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
    def _sanitize_event(event: Mapping[str, Any]) -> Dict[str, Any]:
        blocked = {
            "api_key",
            "provider_client",
            "source_text",
            "translated_text",
            "text",
            "chunks",
        }
        safe = {
            str(key): value
            for key, value in event.items()
            if str(key) not in blocked
        }

        source_text = str(event.get("source_text") or "")
        translated_text = str(event.get("translated_text") or "")

        safe.setdefault("source_chars", len(source_text))
        safe.setdefault("translated_chars", len(translated_text))
        safe.setdefault("metadata", {})
        if isinstance(safe["metadata"], Mapping):
            safe["metadata"] = {
                str(key): value
                for key, value in safe["metadata"].items()
                if str(key) not in blocked
            }
        else:
            safe["metadata"] = {}
        return safe

    @staticmethod
    def _strip_segment_text(plan: Mapping[str, Any]) -> Dict[str, Any]:
        sanitized = dict(plan)
        sanitized["segments"] = [
            {
                key: value
                for key, value in segment.items()
                if key != "text"
            }
            for segment in plan.get("segments", [])
            if isinstance(segment, Mapping)
        ]
        return sanitized


__all__ = ["ReliabilityRuntimeIntegrationAdapter"]
