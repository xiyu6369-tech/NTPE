
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional
from collections import Counter
import re


@dataclass(frozen=True)
class ReliabilityEvent:
    chunk_index: int
    provider: str
    model: str
    source_chars: int
    translated_chars: int
    latency_ms: int
    retry_count: int
    provider_attempts: int
    http_status: Optional[int]
    exception_type: str
    outcome: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class TranslationReliabilityBaseline:
    """Pure reliability classifier and report builder.

    It does not call providers, HTTP clients, launchers, or Translation Runtime.
    It only evaluates caller-supplied metadata and text lengths.
    """

    version = "TE-v4.0"
    stage = "4.0.1"
    name = "translation_reliability_baseline"

    _KNOWN_OUTCOMES = {
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
        "retry_exhausted",
        "unknown_failure",
    }

    def classify(self, sample: Optional[Mapping[str, Any]] = None) -> ReliabilityEvent:
        data = dict(sample or {})
        source_text = str(data.get("source_text") or "")
        translated_text = str(data.get("translated_text") or "")

        source_chars = int(data.get("source_chars", len(source_text)))
        translated_chars = int(data.get("translated_chars", len(translated_text)))
        latency_ms = max(0, int(data.get("latency_ms", 0) or 0))
        retry_count = max(0, int(data.get("retry_count", 0) or 0))
        provider_attempts = max(0, int(data.get("provider_attempts", 0) or 0))
        http_status = data.get("http_status")
        http_status = int(http_status) if http_status not in (None, "") else None
        exception_type = str(data.get("exception_type") or "").strip()
        explicit_outcome = str(data.get("outcome") or "").strip()

        outcome = explicit_outcome or self._infer_outcome(
            source_chars=source_chars,
            translated_chars=translated_chars,
            translated_text=translated_text,
            provider_attempts=provider_attempts,
            http_status=http_status,
            exception_type=exception_type,
            retry_count=retry_count,
            max_retries=int(data.get("max_retries", 0) or 0),
        )

        if outcome not in self._KNOWN_OUTCOMES:
            outcome = "unknown_failure"

        return ReliabilityEvent(
            chunk_index=int(data.get("chunk_index", 0) or 0),
            provider=str(data.get("provider") or "unknown"),
            model=str(data.get("model") or "unknown"),
            source_chars=source_chars,
            translated_chars=translated_chars,
            latency_ms=latency_ms,
            retry_count=retry_count,
            provider_attempts=provider_attempts,
            http_status=http_status,
            exception_type=exception_type,
            outcome=outcome,
            metadata=self._safe_metadata(data.get("metadata")),
        )

    def build_report(self, samples: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
        events = [self.classify(sample) for sample in samples]
        total = len(events)
        success_count = sum(1 for e in events if e.outcome == "success")
        failed_count = total - success_count
        outcome_counts = Counter(e.outcome for e in events)
        provider_counts = Counter(e.provider for e in events)
        model_counts = Counter(e.model for e in events)

        avg_latency = (
            round(sum(e.latency_ms for e in events) / total, 2)
            if total else 0.0
        )
        total_retries = sum(e.retry_count for e in events)
        max_retry = max((e.retry_count for e in events), default=0)
        attempts_zero = sum(1 for e in events if e.provider_attempts == 0)

        success_rate = round((success_count / total) * 100, 2) if total else 0.0
        score = self._score(
            total=total,
            success_count=success_count,
            attempts_zero=attempts_zero,
            total_retries=total_retries,
            outcomes=outcome_counts,
        )

        return {
            "version": self.version,
            "stage": self.stage,
            "baseline": self.name,
            "summary": {
                "total_chunks": total,
                "success_chunks": success_count,
                "failed_chunks": failed_count,
                "success_rate": success_rate,
                "reliability_score": score,
                "avg_latency_ms": avg_latency,
                "total_retries": total_retries,
                "max_retry": max_retry,
                "provider_attempts_zero": attempts_zero,
            },
            "failure_breakdown": dict(sorted(outcome_counts.items())),
            "provider_breakdown": dict(sorted(provider_counts.items())),
            "model_breakdown": dict(sorted(model_counts.items())),
            "events": [self._event_to_dict(e) for e in events],
            "safety": {
                "provider_runtime_modified": False,
                "translation_runtime_modified": False,
                "launcher_modified": False,
                "http_called": False,
                "api_key_accessed": False,
                "real_translation_executed": False,
            },
        }

    def validate_report(self, report: Optional[Mapping[str, Any]]) -> bool:
        if not isinstance(report, Mapping):
            return False
        required = {
            "version",
            "stage",
            "baseline",
            "summary",
            "failure_breakdown",
            "provider_breakdown",
            "model_breakdown",
            "events",
            "safety",
        }
        if not required.issubset(report):
            return False
        if report.get("version") != self.version or report.get("stage") != self.stage:
            return False
        summary = report.get("summary")
        safety = report.get("safety")
        if not isinstance(summary, Mapping) or not isinstance(safety, Mapping):
            return False
        if summary.get("total_chunks", 0) != len(report.get("events", [])):
            return False
        if safety.get("http_called") is not False:
            return False
        if safety.get("api_key_accessed") is not False:
            return False
        if safety.get("real_translation_executed") is not False:
            return False
        return True

    @staticmethod
    def _infer_outcome(
        *,
        source_chars: int,
        translated_chars: int,
        translated_text: str,
        provider_attempts: int,
        http_status: Optional[int],
        exception_type: str,
        retry_count: int,
        max_retries: int,
    ) -> str:
        exc = exception_type.lower()

        if provider_attempts == 0:
            return "provider_not_attempted"
        if http_status == 429:
            return "http_429"
        if http_status == 500:
            return "http_500"
        if http_status == 503:
            return "http_503"
        if "readtimeout" in exc or "read_timeout" in exc:
            return "read_timeout"
        if "connecttimeout" in exc or "connect_timeout" in exc:
            return "connect_timeout"
        if "ssl" in exc:
            return "ssl_error"
        if "json" in exc and "decode" in exc:
            return "json_decode_error"
        if "connection" in exc:
            return "connection_error"
        if translated_chars == 0:
            return "empty_output"
        if source_chars > 0 and translated_chars / source_chars < 0.35:
            return "too_short"
        if re.search(r"[가-힣]", translated_text):
            return "hangul_residue"
        if max_retries > 0 and retry_count >= max_retries and exception_type:
            return "retry_exhausted"
        return "success"

    @staticmethod
    def _score(
        *,
        total: int,
        success_count: int,
        attempts_zero: int,
        total_retries: int,
        outcomes: Mapping[str, int],
    ) -> int:
        if total == 0:
            return 0
        score = 100.0
        failure_rate = (total - success_count) / total
        score -= failure_rate * 70
        score -= min(20, attempts_zero * 8)
        score -= min(10, total_retries * 0.5)
        score -= min(10, outcomes.get("empty_output", 0) * 5)
        score -= min(10, outcomes.get("provider_not_attempted", 0) * 6)
        return max(0, min(100, round(score)))

    @staticmethod
    def _safe_metadata(value: Any) -> Dict[str, Any]:
        if not isinstance(value, Mapping):
            return {}
        blocked = {"api_key", "source_text", "translated_text", "text", "chunks"}
        return {str(k): v for k, v in value.items() if str(k) not in blocked}

    @staticmethod
    def _event_to_dict(event: ReliabilityEvent) -> Dict[str, Any]:
        return {
            "chunk_index": event.chunk_index,
            "provider": event.provider,
            "model": event.model,
            "source_chars": event.source_chars,
            "translated_chars": event.translated_chars,
            "latency_ms": event.latency_ms,
            "retry_count": event.retry_count,
            "provider_attempts": event.provider_attempts,
            "http_status": event.http_status,
            "exception_type": event.exception_type,
            "outcome": event.outcome,
            "metadata": event.metadata,
        }


__all__ = ["ReliabilityEvent", "TranslationReliabilityBaseline"]
