from __future__ import annotations

from typing import Any, Dict, Optional

from .executor_adapter import MockModelAdapter
from .executor_metrics import create_executor_metrics, record_executor_result, executor_metrics_manifest
from .executor_result import create_executor_result, validate_executor_result
from .executor_trace import create_executor_trace, add_executor_event, validate_executor_trace


class TranslationRuntimeExecutor:
    def __init__(self, model_adapter: Optional[Any] = None, executor_id: str = "translation-runtime-executor"):
        self.executor_id = executor_id
        self.model_adapter = model_adapter or MockModelAdapter()
        self.trace = create_executor_trace(executor_id)
        self.metrics = create_executor_metrics()

    def build_prompt_package(self, segment: Dict[str, Any], context_bundle: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        source_text = segment.get("source_text") or segment.get("text") or ""
        return {
            "kind": "ntpe.prompt_package",
            "version": "06.5",
            "segment_id": segment.get("segment_id") or segment.get("id"),
            "source_text": source_text,
            "context_bundle": context_bundle or {},
            "messages": [
                {"role": "system", "content": "Translate the segment using the provided context."},
                {"role": "user", "content": source_text},
            ],
        }

    def execute_segment(
        self,
        job: Dict[str, Any],
        segment: Dict[str, Any],
        context_bundle: Optional[Dict[str, Any]] = None,
        prompt_package: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        job_id = job.get("job_id") or job.get("id") or "job"
        segment_id = segment.get("segment_id") or segment.get("id") or "segment"
        attempts = int(segment.get("attempts", 0)) + 1
        add_executor_event(self.trace, "segment.started", {"job_id": job_id, "segment_id": segment_id})
        segment["status"] = "running"
        segment["attempts"] = attempts
        try:
            package = prompt_package or self.build_prompt_package(segment, context_bundle)
            model_output = self.model_adapter.translate(package)
            output_text = model_output.get("output_text", "")
            segment["status"] = "completed"
            segment["output_text"] = output_text
            result = create_executor_result(
                job_id=job_id,
                segment_id=segment_id,
                output_text=output_text,
                status="completed",
                model=model_output.get("model", "mock"),
                attempts=attempts,
                metadata={"adapter": getattr(self.model_adapter, "adapter_id", "unknown")},
            )
            add_executor_event(self.trace, "segment.completed", {"segment_id": segment_id})
        except Exception as exc:  # noqa: BLE001 - executor normalizes all adapter failures
            segment["status"] = "failed"
            segment["error"] = str(exc)
            result = create_executor_result(
                job_id=job_id,
                segment_id=segment_id,
                status="failed",
                error=str(exc),
                attempts=attempts,
            )
            add_executor_event(self.trace, "segment.failed", {"segment_id": segment_id, "error": str(exc)})
        record_executor_result(self.metrics, result)
        job.setdefault("results", {})[segment_id] = result
        job["last_segment_id"] = segment_id
        return result

    def manifest(self) -> Dict[str, Any]:
        return {
            "kind": "ntpe.translation_runtime_executor",
            "version": "06.5",
            "executor_id": self.executor_id,
            "model_adapter": self.model_adapter.manifest() if hasattr(self.model_adapter, "manifest") else {},
            "trace_valid": validate_executor_trace(self.trace),
            "metrics": executor_metrics_manifest(self.metrics),
            "capabilities": [
                "prompt_package_execution",
                "model_adapter_dispatch",
                "segment_status_update",
                "executor_trace",
                "executor_metrics",
            ],
        }


def create_translation_runtime_executor(model_adapter: Optional[Any] = None) -> TranslationRuntimeExecutor:
    return TranslationRuntimeExecutor(model_adapter=model_adapter)


def validate_translation_executor_result(result: Dict[str, Any]) -> bool:
    return validate_executor_result(result)
