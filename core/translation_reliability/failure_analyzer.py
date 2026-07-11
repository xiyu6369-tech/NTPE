
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Optional


class TranslationFailureAnalyzer:
    """Analyze reliability reports into ranked failure priorities.

    This module is side-effect free. It does not call Provider Runtime,
    Translation Runtime, HTTP clients, launchers, or API keys.
    """

    version = "TE-v4.0"
    stage = "4.0.4"
    name = "translation_failure_analyzer"

    _SEVERITY = {
        "provider_not_attempted": 100,
        "authentication_error": 95,
        "forbidden": 95,
        "http_503": 85,
        "http_429": 80,
        "read_timeout": 75,
        "connect_timeout": 75,
        "connection_error": 70,
        "ssl_error": 70,
        "retry_exhausted": 68,
        "empty_output": 65,
        "too_short": 60,
        "hangul_residue": 58,
        "duplicate_output": 55,
        "json_decode_error": 50,
        "http_500": 50,
        "unknown_failure": 45,
        "success": 0,
    }

    _RECOMMENDATIONS = {
        "provider_not_attempted": "inspect_provider_entry_path_and_rebuild_session",
        "authentication_error": "verify_provider_credentials_without_retry",
        "forbidden": "verify_provider_permissions_without_retry",
        "http_503": "apply_capacity_backoff_and_consider_provider_fallback",
        "http_429": "apply_rate_limit_backoff",
        "read_timeout": "increase_timeout_and_split_chunk",
        "connect_timeout": "increase_connect_timeout_and_retry",
        "connection_error": "rebuild_provider_session",
        "ssl_error": "rebuild_provider_session_and_check_transport",
        "retry_exhausted": "stop_repeating_same_strategy_and_switch_recovery_path",
        "empty_output": "retry_immediately_with_smaller_chunk",
        "too_short": "split_chunk_and_retranslate",
        "hangul_residue": "retranslate_with_smaller_chunk_and_quality_gate",
        "duplicate_output": "retranslate_and_enable_duplicate_guard",
        "json_decode_error": "retry_after_session_rebuild",
        "http_500": "retry_with_backoff",
        "unknown_failure": "capture_exception_details_and_apply_safe_retry",
    }

    def analyze(self, report: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
        data = dict(report or {})
        events = list(data.get("events") or [])
        normalized = [self._normalize_event(event) for event in events if isinstance(event, Mapping)]

        failure_events = [event for event in normalized if event["outcome"] != "success"]
        counts = Counter(event["outcome"] for event in failure_events)

        latency_by_outcome: Dict[str, List[int]] = defaultdict(list)
        retries_by_outcome: Dict[str, int] = defaultdict(int)
        attempts_zero_by_outcome: Dict[str, int] = defaultdict(int)

        for event in failure_events:
            outcome = event["outcome"]
            latency_by_outcome[outcome].append(event["latency_ms"])
            retries_by_outcome[outcome] += event["retry_count"]
            if event["provider_attempts"] == 0:
                attempts_zero_by_outcome[outcome] += 1

        ranked = []
        for outcome, count in counts.items():
            severity = self._SEVERITY.get(outcome, 40)
            avg_latency = (
                round(sum(latency_by_outcome[outcome]) / len(latency_by_outcome[outcome]), 2)
                if latency_by_outcome[outcome]
                else 0.0
            )
            impact_score = self._impact_score(
                severity=severity,
                count=count,
                total_failures=len(failure_events),
                retries=retries_by_outcome[outcome],
                attempts_zero=attempts_zero_by_outcome[outcome],
            )
            ranked.append({
                "outcome": outcome,
                "count": count,
                "severity": severity,
                "impact_score": impact_score,
                "avg_latency_ms": avg_latency,
                "total_retries": retries_by_outcome[outcome],
                "provider_attempts_zero": attempts_zero_by_outcome[outcome],
                "recommendation": self._RECOMMENDATIONS.get(
                    outcome, "capture_more_diagnostics"
                ),
            })

        ranked.sort(
            key=lambda item: (
                -item["impact_score"],
                -item["severity"],
                -item["count"],
                item["outcome"],
            )
        )

        top_failure = ranked[0]["outcome"] if ranked else None
        total_events = len(normalized)
        total_failures = len(failure_events)
        failure_rate = round((total_failures / total_events) * 100, 2) if total_events else 0.0

        return {
            "version": self.version,
            "stage": self.stage,
            "analyzer": self.name,
            "summary": {
                "total_events": total_events,
                "total_failures": total_failures,
                "failure_rate": failure_rate,
                "distinct_failure_types": len(counts),
                "top_failure": top_failure,
                "critical_failures": sum(
                    item["count"] for item in ranked if item["severity"] >= 80
                ),
            },
            "failure_ranking": ranked,
            "priority_actions": [
                {
                    "priority": index,
                    "outcome": item["outcome"],
                    "action": item["recommendation"],
                    "impact_score": item["impact_score"],
                }
                for index, item in enumerate(ranked, start=1)
            ],
            "diagnostics": {
                "provider_attempts_zero_total": sum(
                    event["provider_attempts"] == 0 for event in failure_events
                ),
                "total_retries": sum(event["retry_count"] for event in failure_events),
                "max_latency_ms": max(
                    (event["latency_ms"] for event in failure_events), default=0
                ),
            },
            "safety": {
                "provider_runtime_modified": False,
                "translation_runtime_modified": False,
                "launcher_modified": False,
                "http_called": False,
                "api_key_accessed": False,
                "real_translation_executed": False,
            },
        }

    def validate_analysis(self, analysis: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(analysis, Mapping):
            return False

        required = {
            "version",
            "stage",
            "analyzer",
            "summary",
            "failure_ranking",
            "priority_actions",
            "diagnostics",
            "safety",
        }
        if not required.issubset(analysis):
            return False
        if analysis.get("version") != self.version or analysis.get("stage") != self.stage:
            return False

        summary = analysis.get("summary")
        ranking = analysis.get("failure_ranking")
        actions = analysis.get("priority_actions")
        safety = analysis.get("safety")

        if not isinstance(summary, Mapping):
            return False
        if not isinstance(ranking, list) or not isinstance(actions, list):
            return False
        if not isinstance(safety, Mapping):
            return False
        if len(ranking) != len(actions):
            return False

        previous_score = None
        for index, item in enumerate(ranking, start=1):
            if not isinstance(item, Mapping):
                return False
            if int(item.get("count", 0)) <= 0:
                return False
            score = int(item.get("impact_score", -1))
            if score < 0:
                return False
            if previous_score is not None and score > previous_score:
                return False
            previous_score = score
            if actions[index - 1].get("priority") != index:
                return False
            if actions[index - 1].get("outcome") != item.get("outcome"):
                return False

        if safety.get("http_called") is not False:
            return False
        if safety.get("api_key_accessed") is not False:
            return False
        if safety.get("real_translation_executed") is not False:
            return False

        return True

    @staticmethod
    def _normalize_event(event: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "outcome": str(event.get("outcome") or "unknown_failure"),
            "latency_ms": max(0, int(event.get("latency_ms", 0) or 0)),
            "retry_count": max(0, int(event.get("retry_count", 0) or 0)),
            "provider_attempts": max(0, int(event.get("provider_attempts", 0) or 0)),
        }

    @staticmethod
    def _impact_score(
        *,
        severity: int,
        count: int,
        total_failures: int,
        retries: int,
        attempts_zero: int,
    ) -> int:
        frequency_weight = round((count / total_failures) * 40) if total_failures else 0
        retry_weight = min(15, retries * 2)
        attempts_zero_weight = min(20, attempts_zero * 10)
        score = round(severity * 0.5) + frequency_weight + retry_weight + attempts_zero_weight
        return max(0, min(100, score))


__all__ = ["TranslationFailureAnalyzer"]
