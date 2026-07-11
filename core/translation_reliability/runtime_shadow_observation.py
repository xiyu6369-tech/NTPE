
from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .runtime_integration_adapter import ReliabilityRuntimeIntegrationAdapter


class RuntimeShadowObservation:
    """Observe supplied runtime events without affecting runtime behavior.

    Shadow mode is read-only and analysis-only:
    - no provider calls
    - no HTTP calls
    - no API key access
    - no retry execution
    - no chunk split execution
    - no launcher or Translation Runtime modification
    """

    version = "TE-v4.0"
    stage = "4.0.7"
    name = "runtime_shadow_observation"

    def __init__(self) -> None:
        self.adapter = ReliabilityRuntimeIntegrationAdapter()

    def observe(
        self,
        runtime_events: Optional[Iterable[Mapping[str, Any]]] = None,
        config: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        cfg = self._normalize_config(config)

        if not cfg["enabled"]:
            return self._disabled_result()

        events = [
            dict(event)
            for event in (runtime_events or [])
            if isinstance(event, Mapping)
        ]

        adapter_result = self.adapter.process(
            events,
            {
                "enabled": True,
                "max_attempts": cfg["max_attempts"],
                "base_delay_seconds": cfg["base_delay_seconds"],
                "max_delay_seconds": cfg["max_delay_seconds"],
                "timeout_seconds": cfg["timeout_seconds"],
                "max_timeout_seconds": cfg["max_timeout_seconds"],
                "chunk_size": cfg["chunk_size"],
                "min_chunk_size": cfg["min_chunk_size"],
                "max_chunk_size": cfg["max_chunk_size"],
            },
        )

        baseline = adapter_result.get("baseline_report", {})
        baseline_events = list(baseline.get("events") or [])

        observed_outcomes = Counter(
            str(event.get("outcome") or "unknown_failure")
            for event in baseline_events
        )
        observed_providers = Counter(
            str(event.get("provider") or "unknown")
            for event in baseline_events
        )
        observed_models = Counter(
            str(event.get("model") or "unknown")
            for event in baseline_events
        )

        summary = baseline.get("summary", {})
        failures = int(summary.get("failed_chunks", 0) or 0)
        total = int(summary.get("total_chunks", 0) or 0)

        return {
            "status": "shadow_observation_completed",
            "enabled": True,
            "stage": self.stage,
            "shadow_mode": True,
            "observation_summary": {
                "events_observed": total,
                "success_events": int(summary.get("success_chunks", 0) or 0),
                "failure_events": failures,
                "failure_rate": (
                    round((failures / total) * 100, 2) if total else 0.0
                ),
                "provider_attempts_zero": int(
                    summary.get("provider_attempts_zero", 0) or 0
                ),
                "avg_latency_ms": float(summary.get("avg_latency_ms", 0.0) or 0.0),
                "total_retries": int(summary.get("total_retries", 0) or 0),
            },
            "outcome_breakdown": dict(sorted(observed_outcomes.items())),
            "provider_breakdown": dict(sorted(observed_providers.items())),
            "model_breakdown": dict(sorted(observed_models.items())),
            "adapter_result": adapter_result,
            "shadow_recommendations": self._build_recommendations(adapter_result),
            "integration_status": {
                "mode": "shadow_observation",
                "read_only": True,
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
                "observer": self.name,
                "version": self.version,
                "source_text_retained": False,
                "translated_text_retained": False,
                "event_count": total,
            },
        }

    def validate_result(self, result: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(result, Mapping):
            return False

        required = {
            "status",
            "enabled",
            "stage",
            "shadow_mode",
            "observation_summary",
            "outcome_breakdown",
            "provider_breakdown",
            "model_breakdown",
            "adapter_result",
            "shadow_recommendations",
            "integration_status",
            "metadata",
        }
        if not required.issubset(result):
            return False
        if result.get("stage") != self.stage:
            return False

        integration = result.get("integration_status")
        metadata = result.get("metadata")
        if not isinstance(integration, Mapping) or not isinstance(metadata, Mapping):
            return False

        if integration.get("read_only") is not True:
            return False

        for key in (
            "runtime_modified",
            "provider_called",
            "http_called",
            "api_key_accessed",
            "launcher_modified",
            "retry_executed",
            "split_executed",
            "real_translation_executed",
        ):
            if integration.get(key) is not False:
                return False

        if metadata.get("source_text_retained") is not False:
            return False
        if metadata.get("translated_text_retained") is not False:
            return False

        if result.get("enabled") is False:
            return (
                result.get("status") == "disabled"
                and result.get("adapter_result") == {}
                and result.get("shadow_recommendations") == []
            )

        if result.get("status") != "shadow_observation_completed":
            return False
        if result.get("shadow_mode") is not True:
            return False
        if not self.adapter.validate_result(result.get("adapter_result")):
            return False

        return True

    @staticmethod
    def _build_recommendations(
        adapter_result: Mapping[str, Any]
    ) -> List[Dict[str, Any]]:
        analysis = adapter_result.get("failure_analysis", {})
        actions = analysis.get("priority_actions", [])
        recommendations: List[Dict[str, Any]] = []

        for action in actions[:5]:
            if not isinstance(action, Mapping):
                continue
            recommendations.append({
                "priority": int(action.get("priority", 0) or 0),
                "outcome": str(action.get("outcome") or "unknown_failure"),
                "recommended_action": str(
                    action.get("action") or "capture_more_diagnostics"
                ),
                "execute_automatically": False,
                "shadow_only": True,
            })

        return recommendations

    @staticmethod
    def _normalize_config(config: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
        src = dict(config or {})
        return {
            "enabled": src.get("enabled") is True,
            "max_attempts": max(1, int(src.get("max_attempts", 5) or 5)),
            "base_delay_seconds": max(
                0, int(src.get("base_delay_seconds", 5) or 5)
            ),
            "max_delay_seconds": max(
                1, int(src.get("max_delay_seconds", 60) or 60)
            ),
            "timeout_seconds": max(
                1, int(src.get("timeout_seconds", 180) or 180)
            ),
            "max_timeout_seconds": max(
                1, int(src.get("max_timeout_seconds", 300) or 300)
            ),
            "chunk_size": max(1, int(src.get("chunk_size", 600) or 600)),
            "min_chunk_size": max(
                1, int(src.get("min_chunk_size", 200) or 200)
            ),
            "max_chunk_size": max(
                1, int(src.get("max_chunk_size", 1200) or 1200)
            ),
        }

    def _disabled_result(self) -> Dict[str, Any]:
        return {
            "status": "disabled",
            "enabled": False,
            "stage": self.stage,
            "shadow_mode": True,
            "observation_summary": {
                "events_observed": 0,
                "success_events": 0,
                "failure_events": 0,
                "failure_rate": 0.0,
                "provider_attempts_zero": 0,
                "avg_latency_ms": 0.0,
                "total_retries": 0,
            },
            "outcome_breakdown": {},
            "provider_breakdown": {},
            "model_breakdown": {},
            "adapter_result": {},
            "shadow_recommendations": [],
            "integration_status": {
                "mode": "disabled",
                "read_only": True,
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
                "observer": self.name,
                "version": self.version,
                "source_text_retained": False,
                "translated_text_retained": False,
                "event_count": 0,
            },
        }


__all__ = ["RuntimeShadowObservation"]
