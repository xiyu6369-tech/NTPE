"""NTPE Foundation-06.1 Translation Job Manager.

Incremental management layer for Foundation-06.0 translation contracts.
This module is intentionally dependency-light and dictionary-compatible so it can
work with existing contract dictionaries without requiring destructive changes.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional

VERSION = "Foundation-06.1"

SEGMENT_PENDING = "pending"
SEGMENT_RUNNING = "running"
SEGMENT_COMPLETED = "completed"
SEGMENT_FAILED = "failed"
SEGMENT_SKIPPED = "skipped"

VALID_SEGMENT_STATUSES = {
    SEGMENT_PENDING,
    SEGMENT_RUNNING,
    SEGMENT_COMPLETED,
    SEGMENT_FAILED,
    SEGMENT_SKIPPED,
}

JOB_PENDING = "pending"
JOB_RUNNING = "running"
JOB_COMPLETED = "completed"
JOB_FAILED = "failed"
JOB_PARTIAL = "partial"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_progress(total: int = 0, completed: int = 0, failed: int = 0, skipped: int = 0) -> Dict[str, Any]:
    pending = max(total - completed - failed - skipped, 0)
    percent = 0.0 if total <= 0 else round((completed + skipped) / total * 100, 2)
    return {
        "total": total,
        "pending": pending,
        "running": 0,
        "completed": completed,
        "failed": failed,
        "skipped": skipped,
        "percent": percent,
    }


def normalize_segment(segment: Dict[str, Any], index: Optional[int] = None) -> Dict[str, Any]:
    data = deepcopy(segment or {})
    idx = data.get("index", index if index is not None else 0)
    data.setdefault("segment_id", data.get("id", f"segment-{idx}"))
    data.setdefault("index", idx)
    data.setdefault("source_text", data.get("text", ""))
    data.setdefault("target_text", data.get("output", ""))
    data.setdefault("status", SEGMENT_PENDING)
    data.setdefault("attempts", 0)
    data.setdefault("errors", [])
    data.setdefault("metadata", {})
    data.setdefault("created_at", _now())
    data.setdefault("updated_at", data["created_at"])
    return data


def validate_segment(segment: Dict[str, Any]) -> bool:
    if not isinstance(segment, dict):
        return False
    if not segment.get("segment_id"):
        return False
    if segment.get("status") not in VALID_SEGMENT_STATUSES:
        return False
    if not isinstance(segment.get("attempts", 0), int):
        return False
    return True


def create_job(job_id: str, segments: Iterable[Dict[str, Any]], source_language: str = "ko", target_language: str = "zh-TW", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    normalized_segments = [normalize_segment(seg, i) for i, seg in enumerate(segments)]
    job = {
        "job_id": job_id,
        "version": VERSION,
        "source_language": source_language,
        "target_language": target_language,
        "status": JOB_PENDING,
        "segments": normalized_segments,
        "progress": create_progress(total=len(normalized_segments)),
        "metadata": metadata or {},
        "events": [],
        "created_at": _now(),
        "updated_at": _now(),
    }
    add_job_event(job, "job_created", {"segments": len(normalized_segments)})
    return job


def normalize_job(job: Dict[str, Any]) -> Dict[str, Any]:
    data = deepcopy(job or {})
    data.setdefault("job_id", data.get("id", "translation-job"))
    data.setdefault("version", VERSION)
    data.setdefault("source_language", "ko")
    data.setdefault("target_language", "zh-TW")
    data.setdefault("status", JOB_PENDING)
    data["segments"] = [normalize_segment(seg, i) for i, seg in enumerate(data.get("segments", []))]
    data.setdefault("metadata", {})
    data.setdefault("events", [])
    data.setdefault("created_at", _now())
    data.setdefault("updated_at", data["created_at"])
    data["progress"] = calculate_progress(data)
    return data


def validate_job(job: Dict[str, Any]) -> bool:
    if not isinstance(job, dict) or not job.get("job_id"):
        return False
    if not isinstance(job.get("segments"), list):
        return False
    return all(validate_segment(seg) for seg in job["segments"])


def add_job_event(job: Dict[str, Any], event_type: str, detail: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    event = {"type": event_type, "detail": detail or {}, "timestamp": _now()}
    job.setdefault("events", []).append(event)
    job["updated_at"] = event["timestamp"]
    return event


def get_segment(job: Dict[str, Any], segment_id: str) -> Optional[Dict[str, Any]]:
    for seg in job.get("segments", []):
        if seg.get("segment_id") == segment_id:
            return seg
    return None


def update_segment_status(job: Dict[str, Any], segment_id: str, status: str, target_text: Optional[str] = None, error: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if status not in VALID_SEGMENT_STATUSES:
        raise ValueError(f"invalid segment status: {status}")
    seg = get_segment(job, segment_id)
    if seg is None:
        raise KeyError(f"segment not found: {segment_id}")
    seg["status"] = status
    seg["updated_at"] = _now()
    if status == SEGMENT_RUNNING:
        seg["attempts"] = int(seg.get("attempts", 0)) + 1
    if target_text is not None:
        seg["target_text"] = target_text
    if error is not None:
        seg.setdefault("errors", []).append(error)
    job["progress"] = calculate_progress(job)
    job["status"] = infer_job_status(job)
    add_job_event(job, "segment_updated", {"segment_id": segment_id, "status": status})
    return seg


def calculate_progress(job: Dict[str, Any]) -> Dict[str, Any]:
    counts = {s: 0 for s in VALID_SEGMENT_STATUSES}
    for seg in job.get("segments", []):
        counts[seg.get("status", SEGMENT_PENDING)] = counts.get(seg.get("status", SEGMENT_PENDING), 0) + 1
    total = len(job.get("segments", []))
    percent = 0.0 if total <= 0 else round((counts[SEGMENT_COMPLETED] + counts[SEGMENT_SKIPPED]) / total * 100, 2)
    return {
        "total": total,
        "pending": counts[SEGMENT_PENDING],
        "running": counts[SEGMENT_RUNNING],
        "completed": counts[SEGMENT_COMPLETED],
        "failed": counts[SEGMENT_FAILED],
        "skipped": counts[SEGMENT_SKIPPED],
        "percent": percent,
    }


def infer_job_status(job: Dict[str, Any]) -> str:
    p = calculate_progress(job)
    if p["running"] > 0:
        return JOB_RUNNING
    if p["failed"] > 0 and p["completed"] + p["skipped"] == 0:
        return JOB_FAILED
    if p["failed"] > 0:
        return JOB_PARTIAL
    if p["total"] > 0 and p["completed"] + p["skipped"] == p["total"]:
        return JOB_COMPLETED
    return JOB_PENDING


def export_job_manifest(job: Dict[str, Any]) -> Dict[str, Any]:
    normalized = normalize_job(job)
    return {
        "type": "translation_job_manifest",
        "version": VERSION,
        "job_id": normalized["job_id"],
        "status": normalized["status"],
        "source_language": normalized["source_language"],
        "target_language": normalized["target_language"],
        "progress": normalized["progress"],
        "segment_ids": [seg["segment_id"] for seg in normalized["segments"]],
        "event_count": len(normalized.get("events", [])),
        "metadata": normalized.get("metadata", {}),
    }


class TranslationJobManager:
    def __init__(self, job: Optional[Dict[str, Any]] = None):
        self.job = normalize_job(job) if job is not None else None

    def create(self, job_id: str, segments: Iterable[Dict[str, Any]], source_language: str = "ko", target_language: str = "zh-TW", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.job = create_job(job_id, segments, source_language, target_language, metadata)
        return self.job

    def load(self, job: Dict[str, Any]) -> Dict[str, Any]:
        self.job = normalize_job(job)
        add_job_event(self.job, "job_loaded")
        return self.job

    def update_segment(self, segment_id: str, status: str, target_text: Optional[str] = None, error: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.job is None:
            raise RuntimeError("job is not loaded")
        return update_segment_status(self.job, segment_id, status, target_text, error)

    def progress(self) -> Dict[str, Any]:
        if self.job is None:
            return create_progress()
        self.job["progress"] = calculate_progress(self.job)
        return self.job["progress"]

    def manifest(self) -> Dict[str, Any]:
        if self.job is None:
            raise RuntimeError("job is not loaded")
        return export_job_manifest(self.job)

    def next_pending(self) -> Optional[Dict[str, Any]]:
        if self.job is None:
            return None
        for seg in self.job.get("segments", []):
            if seg.get("status") == SEGMENT_PENDING:
                return seg
        return None


class TranslationJobManagerAdapter:
    def __init__(self, manager: Optional[TranslationJobManager] = None):
        self.manager = manager or TranslationJobManager()

    def create_job(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return self.manager.create(*args, **kwargs)

    def load_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        return self.manager.load(job)

    def update(self, segment_id: str, status: str, target_text: Optional[str] = None, error: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.manager.update_segment(segment_id, status, target_text, error)

    def validate(self, job: Optional[Dict[str, Any]] = None) -> bool:
        return validate_job(job or self.manager.job or {})

    def manifest(self) -> Dict[str, Any]:
        return self.manager.manifest()


def create_translation_job_manager(job: Optional[Dict[str, Any]] = None) -> TranslationJobManager:
    return TranslationJobManager(job)


def create_translation_job_manager_adapter(job: Optional[Dict[str, Any]] = None) -> TranslationJobManagerAdapter:
    return TranslationJobManagerAdapter(TranslationJobManager(job))
