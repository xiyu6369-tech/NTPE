"""NTPE Foundation-06.6 Translation Runtime Core.

This module integrates Foundation-06.0 through 06.5 into a single runtime entry
point. It is intentionally dictionary-compatible and additive: older job,
segment, context, prompt, and executor dictionaries are preserved and normalized
without requiring destructive migrations.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

VERSION = "Foundation-06.6"
SESSION_TYPE = "translation_runtime_session"
RUNTIME_RESULT_TYPE = "translation_runtime_core_result"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _job_id(job: Dict[str, Any]) -> str:
    return str(job.get("job_id") or job.get("id") or "job")


def _segment_id(segment: Dict[str, Any], index: int = 0) -> str:
    return str(segment.get("segment_id") or segment.get("id") or f"segment-{index}")


def _normalize_segment(segment: Dict[str, Any], index: int = 0) -> Dict[str, Any]:
    data = deepcopy(segment or {})
    data.setdefault("segment_id", _segment_id(data, index))
    data.setdefault("index", int(data.get("index", index)))
    data.setdefault("source_text", data.get("text", ""))
    data.setdefault("target_text", data.get("output", data.get("output_text", "")))
    data.setdefault("status", "pending")
    data.setdefault("attempts", 0)
    data.setdefault("metadata", {})
    return data


def normalize_runtime_job(job: Dict[str, Any]) -> Dict[str, Any]:
    data = deepcopy(job or {})
    data.setdefault("job_id", _job_id(data))
    data.setdefault("source_language", data.get("source", "auto"))
    data.setdefault("target_language", data.get("target", "zh-TW"))
    data.setdefault("status", "pending")
    data.setdefault("metadata", {})
    segments = data.get("segments", [])
    data["segments"] = [_normalize_segment(seg, idx) for idx, seg in enumerate(segments)]
    data.setdefault("results", {})
    return data


def create_translation_session(job: Dict[str, Any], session_id: Optional[str] = None, status: str = "created") -> Dict[str, Any]:
    normalized = normalize_runtime_job(job)
    jid = normalized["job_id"]
    total = len(normalized.get("segments", []))
    return {
        "type": SESSION_TYPE,
        "version": VERSION,
        "session_id": session_id or f"session::{jid}",
        "job_id": jid,
        "status": status,
        "created_at": _now(),
        "updated_at": _now(),
        "current_segment_id": None,
        "resume": {"enabled": True, "completed_segment_ids": [], "failed_segment_ids": [], "last_segment_id": None},
        "progress": {"total": total, "completed": 0, "failed": 0, "skipped": 0, "percent": 0.0},
        "events": [],
        "metadata": deepcopy(normalized.get("metadata", {})),
    }


def validate_translation_session(session: Dict[str, Any]) -> bool:
    return isinstance(session, dict) and session.get("type") == SESSION_TYPE and bool(session.get("session_id")) and bool(session.get("job_id")) and isinstance(session.get("progress"), dict)


def add_runtime_event(session: Dict[str, Any], event: str, **data: Any) -> Dict[str, Any]:
    session.setdefault("events", []).append({"event": event, "timestamp": _now(), **deepcopy(data)})
    session["updated_at"] = _now()
    return session


def update_session_progress(session: Dict[str, Any], segments: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    items = list(segments or [])
    total = len(items)
    completed = len([s for s in items if s.get("status") == "completed"])
    failed = len([s for s in items if s.get("status") == "failed"])
    skipped = len([s for s in items if s.get("status") == "skipped"])
    finished = completed + failed + skipped
    session["progress"] = {
        "total": total,
        "completed": completed,
        "failed": failed,
        "skipped": skipped,
        "percent": 100.0 if total == 0 else round((finished / total) * 100, 2),
    }
    session.setdefault("resume", {})["completed_segment_ids"] = [s.get("segment_id") for s in items if s.get("status") == "completed"]
    session.setdefault("resume", {})["failed_segment_ids"] = [s.get("segment_id") for s in items if s.get("status") == "failed"]
    session["updated_at"] = _now()
    return session


class TranslationRuntimeCore:
    """Single public runtime entry point for Foundation-06 Translation Runtime."""

    def __init__(
        self,
        context_adapter: Optional[Any] = None,
        prompt_adapter: Optional[Any] = None,
        executor_adapter: Optional[Any] = None,
        runtime_id: str = "translation-runtime-core",
    ) -> None:
        self.runtime_id = runtime_id
        self.context_adapter = context_adapter or self._default_context_adapter()
        self.prompt_adapter = prompt_adapter or self._default_prompt_adapter()
        self.executor_adapter = executor_adapter or self._default_executor_adapter()
        self.events: List[Dict[str, Any]] = []
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def _event(self, event: str, **data: Any) -> None:
        self.events.append({"event": event, "timestamp": _now(), **deepcopy(data)})

    @staticmethod
    def _default_context_adapter() -> Any:
        try:
            from translation.context_runtime import create_translation_context_runtime_adapter

            return create_translation_context_runtime_adapter(window=1)
        except Exception:  # pragma: no cover - incremental fallback
            class FallbackContextAdapter:
                def build_context(self, segment: Dict[str, Any], segments: Optional[Iterable[Dict[str, Any]]] = None, **kwargs: Any) -> Dict[str, Any]:
                    return {"type": "translation_context_bundle", "context_id": f"context::{segment.get('segment_id', 'segment')}", "segment": deepcopy(segment), "job": deepcopy(kwargs.get("job", {})), "previous_context": [], "next_context": [], "glossary_context": deepcopy(kwargs.get("glossary", {}))}

                def manifest(self) -> Dict[str, Any]:
                    return {"type": "fallback_context_adapter"}

            return FallbackContextAdapter()

    @staticmethod
    def _default_prompt_adapter() -> Any:
        try:
            from translation.prompt_runtime import create_prompt_runtime_adapter

            return create_prompt_runtime_adapter()
        except Exception:  # pragma: no cover
            class FallbackPromptAdapter:
                def build_prompt(self, context_bundle: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
                    segment = context_bundle.get("segment", {})
                    text = segment.get("source_text", "")
                    return {"type": "translation_prompt_package", "package_id": f"prompt::{segment.get('segment_id', 'segment')}", "source_text": text, "messages": [{"role": "user", "content": text}], "prompt_text": text}

                def manifest(self) -> Dict[str, Any]:
                    return {"type": "fallback_prompt_adapter"}

            return FallbackPromptAdapter()

    @staticmethod
    def _default_executor_adapter() -> Any:
        try:
            from translation.executor import TranslationRuntimeExecutor, TranslationExecutorAdapter

            return TranslationExecutorAdapter(TranslationRuntimeExecutor())
        except Exception:  # pragma: no cover
            class FallbackExecutorAdapter:
                def execute(self, job: Dict[str, Any], segment: Dict[str, Any], context_bundle: Optional[Dict[str, Any]] = None, prompt_package: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
                    segment["status"] = "completed"
                    output_text = f"[translated] {segment.get('source_text', '')}".strip()
                    segment["output_text"] = output_text
                    return {"type": "executor_result", "job_id": job.get("job_id", "job"), "segment_id": segment.get("segment_id", "segment"), "status": "completed", "output_text": output_text}

                def manifest(self) -> Dict[str, Any]:
                    return {"type": "fallback_executor_adapter"}

            return FallbackExecutorAdapter()

    def bootstrap(self) -> Dict[str, Any]:
        self._event("runtime_bootstrap", runtime_id=self.runtime_id)
        return self.manifest()

    def create_session(self, job: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
        session = create_translation_session(job, session_id=session_id)
        self.sessions[session["session_id"]] = session
        self._event("session_created", session_id=session["session_id"], job_id=session["job_id"])
        return session

    def resume_session(self, session: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
        normalized = normalize_runtime_job(job)
        update_session_progress(session, normalized.get("segments", []))
        session["status"] = "resumed"
        add_runtime_event(session, "session_resumed", job_id=normalized["job_id"])
        self.sessions[session["session_id"]] = session
        return session

    def execute(self, job: Dict[str, Any], session: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        runtime_job = normalize_runtime_job(job)
        segments = runtime_job.get("segments", [])
        active_session = session or self.create_session(runtime_job, session_id=kwargs.get("session_id"))
        active_session["status"] = "running"
        add_runtime_event(active_session, "session_started", job_id=runtime_job["job_id"])
        self._event("runtime_execute_started", job_id=runtime_job["job_id"])

        results: List[Dict[str, Any]] = []
        try:
            for segment in segments:
                sid = segment["segment_id"]
                if segment.get("status") == "completed" and kwargs.get("resume", True):
                    add_runtime_event(active_session, "segment_skipped_completed", segment_id=sid)
                    continue
                active_session["current_segment_id"] = sid
                active_session.setdefault("resume", {})["last_segment_id"] = sid
                add_runtime_event(active_session, "segment_started", segment_id=sid)

                context_bundle = self.context_adapter.build_context(
                    segment,
                    segments,
                    job=runtime_job,
                    glossary=kwargs.get("glossary", runtime_job.get("glossary", {})),
                    character_context=kwargs.get("character_context", runtime_job.get("character_context", {})),
                    narrative_context=kwargs.get("narrative_context", runtime_job.get("narrative_context", {})),
                    scene_context=kwargs.get("scene_context", runtime_job.get("scene_context", {})),
                    pipeline_context=kwargs.get("pipeline_context", {}),
                )
                prompt_package = self.prompt_adapter.build_prompt(context_bundle)
                result = self.executor_adapter.execute(runtime_job, segment, context_bundle=context_bundle, prompt_package=prompt_package)
                results.append(result)
                add_runtime_event(active_session, f"segment_{result.get('status', 'completed')}", segment_id=sid)
                update_session_progress(active_session, segments)

            update_session_progress(active_session, segments)
            active_session["status"] = "completed" if active_session["progress"].get("failed", 0) == 0 else "partial"
            add_runtime_event(active_session, "session_completed", status=active_session["status"])
            self._event("runtime_execute_completed", job_id=runtime_job["job_id"], status=active_session["status"])
            status = active_session["status"]
            error = None
        except Exception as exc:  # noqa: BLE001 - runtime normalizes pipeline failures
            active_session["status"] = "failed"
            active_session["error"] = str(exc)
            add_runtime_event(active_session, "session_failed", error=str(exc))
            self._event("runtime_execute_failed", job_id=runtime_job["job_id"], error=str(exc))
            status = "failed"
            error = str(exc)

        runtime_result = {
            "type": RUNTIME_RESULT_TYPE,
            "version": VERSION,
            "runtime_id": self.runtime_id,
            "job": runtime_job,
            "session": deepcopy(active_session),
            "results": deepcopy(results),
            "status": status,
            "error": error,
            "created_at": _now(),
            "manifest": self.manifest(),
        }
        return runtime_result

    def manifest(self) -> Dict[str, Any]:
        return create_translation_runtime_core_manifest(
            runtime_id=self.runtime_id,
            events=self.events,
            context_manifest=self.context_adapter.manifest() if hasattr(self.context_adapter, "manifest") else {},
            prompt_manifest=self.prompt_adapter.manifest() if hasattr(self.prompt_adapter, "manifest") else {},
            executor_manifest=self.executor_adapter.manifest() if hasattr(self.executor_adapter, "manifest") else {},
            sessions=list(self.sessions.keys()),
        )


def validate_runtime_result(result: Dict[str, Any]) -> bool:
    return isinstance(result, dict) and result.get("type") == RUNTIME_RESULT_TYPE and result.get("status") in {"completed", "partial", "failed"} and validate_translation_session(result.get("session", {}))


def create_translation_runtime_core_manifest(
    runtime_id: str = "translation-runtime-core",
    events: Optional[List[Dict[str, Any]]] = None,
    context_manifest: Optional[Dict[str, Any]] = None,
    prompt_manifest: Optional[Dict[str, Any]] = None,
    executor_manifest: Optional[Dict[str, Any]] = None,
    sessions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "name": "NTPE Foundation-06.6 Translation Runtime Core",
        "version": VERSION,
        "type": "translation_runtime_core",
        "runtime_id": runtime_id,
        "capabilities": [
            "runtime_bootstrap",
            "translation_session",
            "session_resume",
            "context_runtime_integration",
            "prompt_runtime_integration",
            "executor_integration",
            "runtime_events",
            "runtime_manifest",
        ],
        "events": deepcopy(events or []),
        "sessions": deepcopy(sessions or []),
        "components": {
            "context_runtime": deepcopy(context_manifest or {}),
            "prompt_runtime": deepcopy(prompt_manifest or {}),
            "executor": deepcopy(executor_manifest or {}),
        },
        "compatible_with": ["Foundation-06.5", "Foundation-06.4", "Foundation-06.3", "Foundation-06.2", "Foundation-06.1", "Foundation-06.0", "Foundation-05.6"],
    }


class TranslationRuntimeCoreAdapter:
    def __init__(self, runtime: Optional[TranslationRuntimeCore] = None) -> None:
        self.runtime = runtime or TranslationRuntimeCore()

    def run(self, job: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        return self.runtime.execute(job, **kwargs)

    def create_session(self, job: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        return self.runtime.create_session(job, **kwargs)

    def validate(self, result: Dict[str, Any]) -> bool:
        return validate_runtime_result(result)

    def manifest(self) -> Dict[str, Any]:
        return self.runtime.manifest()


def create_translation_runtime(runtime_id: str = "translation-runtime-core", **kwargs: Any) -> TranslationRuntimeCore:
    return TranslationRuntimeCore(runtime_id=runtime_id, **kwargs)


def create_translation_runtime_adapter(**kwargs: Any) -> TranslationRuntimeCoreAdapter:
    return TranslationRuntimeCoreAdapter(create_translation_runtime(**kwargs))
