"""NTPE Foundation-06.2 Translation Segment Manager.

Incremental segment orchestration layer for Foundation-06.x translation runtime.
This module is dictionary-compatible and intentionally non-destructive: segment
payloads are normalized by copying, and existing unknown fields are preserved.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:  # keep this module usable even when copied alone during incremental updates
    from .job_manager import (
        SEGMENT_COMPLETED,
        SEGMENT_FAILED,
        SEGMENT_PENDING,
        SEGMENT_RUNNING,
        SEGMENT_SKIPPED,
        VALID_SEGMENT_STATUSES,
        normalize_segment,
        validate_segment,
    )
except Exception:  # pragma: no cover
    SEGMENT_PENDING = "pending"
    SEGMENT_RUNNING = "running"
    SEGMENT_COMPLETED = "completed"
    SEGMENT_FAILED = "failed"
    SEGMENT_SKIPPED = "skipped"
    VALID_SEGMENT_STATUSES = {SEGMENT_PENDING, SEGMENT_RUNNING, SEGMENT_COMPLETED, SEGMENT_FAILED, SEGMENT_SKIPPED}

    def normalize_segment(segment: Dict[str, Any], index: Optional[int] = None) -> Dict[str, Any]:
        data = dict(segment or {})
        idx = data.get("index", index if index is not None else 0)
        data.setdefault("segment_id", data.get("id", f"segment-{idx}"))
        data.setdefault("index", idx)
        data.setdefault("source_text", data.get("text", ""))
        data.setdefault("target_text", data.get("output", ""))
        data.setdefault("status", SEGMENT_PENDING)
        data.setdefault("attempts", 0)
        data.setdefault("errors", [])
        data.setdefault("metadata", {})
        return data

    def validate_segment(segment: Dict[str, Any]) -> bool:
        return isinstance(segment, dict) and bool(segment.get("segment_id")) and segment.get("status") in VALID_SEGMENT_STATUSES

VERSION = "Foundation-06.2"

QUEUE_PENDING = "pending"
QUEUE_READY = "ready"
QUEUE_BLOCKED = "blocked"
QUEUE_EMPTY = "empty"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_managed_segment(segment: Dict[str, Any], index: Optional[int] = None, priority: int = 100) -> Dict[str, Any]:
    data = normalize_segment(deepcopy(segment or {}), index)
    data.setdefault("priority", int(data.get("metadata", {}).get("priority", priority)))
    data.setdefault("dependencies", list(data.get("requires", data.get("dependencies", [])) or []))
    data.setdefault("retry", {"attempts": int(data.get("attempts", 0)), "max_attempts": int(data.get("max_attempts", 3))})
    data.setdefault("split_from", data.get("metadata", {}).get("split_from"))
    data.setdefault("merge_group", data.get("metadata", {}).get("merge_group"))
    data.setdefault("queue_status", QUEUE_PENDING)
    data.setdefault("metrics", {"source_length": len(data.get("source_text", "")), "target_length": len(data.get("target_text", ""))})
    data.setdefault("updated_at", _now())
    return data


def validate_managed_segment(segment: Dict[str, Any]) -> bool:
    if not validate_segment(segment):
        return False
    if not isinstance(segment.get("priority", 100), int):
        return False
    if not isinstance(segment.get("dependencies", []), list):
        return False
    if not isinstance(segment.get("retry", {}), dict):
        return False
    return True


def sort_segments(segments: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = [normalize_managed_segment(seg, i) for i, seg in enumerate(segments)]
    return sorted(normalized, key=lambda s: (int(s.get("priority", 100)), int(s.get("index", 0)), str(s.get("segment_id", ""))))


def create_segment_queue(segments: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    ordered = sort_segments(segments)
    queue = {
        "type": "translation_segment_queue",
        "version": VERSION,
        "status": QUEUE_READY if ordered else QUEUE_EMPTY,
        "segments": ordered,
        "cursor": 0,
        "events": [],
        "created_at": _now(),
        "updated_at": _now(),
    }
    add_queue_event(queue, "queue_created", {"segments": len(ordered)})
    return queue


def add_queue_event(queue: Dict[str, Any], event_type: str, detail: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    event = {"type": event_type, "detail": detail or {}, "timestamp": _now()}
    queue.setdefault("events", []).append(event)
    queue["updated_at"] = event["timestamp"]
    return event


def completed_segment_ids(queue: Dict[str, Any]) -> set:
    return {seg.get("segment_id") for seg in queue.get("segments", []) if seg.get("status") in {SEGMENT_COMPLETED, SEGMENT_SKIPPED}}


def is_segment_blocked(segment: Dict[str, Any], done_ids: Optional[set] = None) -> bool:
    done_ids = done_ids or set()
    return any(dep not in done_ids for dep in segment.get("dependencies", []) or [])


def next_ready_segment(queue: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    done = completed_segment_ids(queue)
    for seg in queue.get("segments", []):
        if seg.get("status") != SEGMENT_PENDING:
            continue
        if is_segment_blocked(seg, done):
            seg["queue_status"] = QUEUE_BLOCKED
            continue
        seg["queue_status"] = QUEUE_READY
        return seg
    return None


def mark_segment_running(segment: Dict[str, Any]) -> Dict[str, Any]:
    segment["status"] = SEGMENT_RUNNING
    segment["attempts"] = int(segment.get("attempts", 0)) + 1
    segment.setdefault("retry", {})["attempts"] = int(segment.get("retry", {}).get("attempts", 0)) + 1
    segment["updated_at"] = _now()
    return segment


def can_retry_segment(segment: Dict[str, Any]) -> bool:
    retry = segment.get("retry", {})
    attempts = int(retry.get("attempts", segment.get("attempts", 0)))
    max_attempts = int(retry.get("max_attempts", 3))
    return attempts < max_attempts


def mark_segment_failed(segment: Dict[str, Any], error: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if error is not None:
        segment.setdefault("errors", []).append(error)
    segment["status"] = SEGMENT_PENDING if can_retry_segment(segment) else SEGMENT_FAILED
    segment["queue_status"] = QUEUE_PENDING if segment["status"] == SEGMENT_PENDING else QUEUE_BLOCKED
    segment["updated_at"] = _now()
    return segment


def complete_segment(segment: Dict[str, Any], target_text: str) -> Dict[str, Any]:
    segment["status"] = SEGMENT_COMPLETED
    segment["target_text"] = target_text
    segment.setdefault("metrics", {})["target_length"] = len(target_text or "")
    segment["queue_status"] = QUEUE_READY
    segment["updated_at"] = _now()
    return segment


def split_segment(segment: Dict[str, Any], max_length: int = 1000) -> List[Dict[str, Any]]:
    source = segment.get("source_text", "") or ""
    if max_length <= 0 or len(source) <= max_length:
        return [normalize_managed_segment(segment, segment.get("index", 0))]
    parts = [source[i:i + max_length] for i in range(0, len(source), max_length)]
    parent_id = segment.get("segment_id", "segment")
    base_index = int(segment.get("index", 0))
    result = []
    for offset, part in enumerate(parts):
        child = deepcopy(segment)
        child["segment_id"] = f"{parent_id}.{offset + 1}"
        child["index"] = base_index + offset
        child["source_text"] = part
        child["target_text"] = ""
        child["status"] = SEGMENT_PENDING
        child["split_from"] = parent_id
        child["merge_group"] = parent_id
        child.setdefault("metadata", {})["split_from"] = parent_id
        child["metadata"]["split_index"] = offset
        child["metrics"] = {"source_length": len(part), "target_length": 0}
        result.append(normalize_managed_segment(child, child["index"]))
    return result


def merge_segments(segments: Iterable[Dict[str, Any]], separator: str = "") -> Dict[str, Any]:
    ordered = sorted([normalize_managed_segment(seg) for seg in segments], key=lambda s: int(s.get("index", 0)))
    group = ordered[0].get("merge_group") if ordered else None
    return {
        "type": "translation_segment_merge",
        "version": VERSION,
        "merge_group": group,
        "segment_ids": [seg.get("segment_id") for seg in ordered],
        "target_text": separator.join(seg.get("target_text", "") for seg in ordered),
        "completed": all(seg.get("status") == SEGMENT_COMPLETED for seg in ordered),
        "count": len(ordered),
    }


def queue_metrics(queue: Dict[str, Any]) -> Dict[str, Any]:
    counts = {status: 0 for status in VALID_SEGMENT_STATUSES}
    for seg in queue.get("segments", []):
        status = seg.get("status", SEGMENT_PENDING)
        counts[status] = counts.get(status, 0) + 1
    total = len(queue.get("segments", []))
    return {
        "total": total,
        "pending": counts.get(SEGMENT_PENDING, 0),
        "running": counts.get(SEGMENT_RUNNING, 0),
        "completed": counts.get(SEGMENT_COMPLETED, 0),
        "failed": counts.get(SEGMENT_FAILED, 0),
        "skipped": counts.get(SEGMENT_SKIPPED, 0),
        "percent": 0.0 if total == 0 else round((counts.get(SEGMENT_COMPLETED, 0) + counts.get(SEGMENT_SKIPPED, 0)) / total * 100, 2),
    }


def export_segment_manifest(queue: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": "translation_segment_manifest",
        "version": VERSION,
        "status": queue.get("status", QUEUE_PENDING),
        "metrics": queue_metrics(queue),
        "segment_ids": [seg.get("segment_id") for seg in queue.get("segments", [])],
        "blocked_ids": [seg.get("segment_id") for seg in queue.get("segments", []) if seg.get("queue_status") == QUEUE_BLOCKED],
        "event_count": len(queue.get("events", [])),
    }


class TranslationSegmentManager:
    def __init__(self, segments: Optional[Iterable[Dict[str, Any]]] = None):
        self.queue = create_segment_queue(segments or [])

    def load(self, segments: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        self.queue = create_segment_queue(segments)
        add_queue_event(self.queue, "queue_loaded", {"segments": len(self.queue.get("segments", []))})
        return self.queue

    def next(self) -> Optional[Dict[str, Any]]:
        seg = next_ready_segment(self.queue)
        if seg is not None:
            add_queue_event(self.queue, "segment_ready", {"segment_id": seg.get("segment_id")})
        return seg

    def start(self, segment_id: str) -> Dict[str, Any]:
        seg = self.get(segment_id)
        mark_segment_running(seg)
        add_queue_event(self.queue, "segment_running", {"segment_id": segment_id})
        return seg

    def complete(self, segment_id: str, target_text: str) -> Dict[str, Any]:
        seg = self.get(segment_id)
        complete_segment(seg, target_text)
        add_queue_event(self.queue, "segment_completed", {"segment_id": segment_id})
        return seg

    def fail(self, segment_id: str, error: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        seg = self.get(segment_id)
        mark_segment_failed(seg, error)
        add_queue_event(self.queue, "segment_failed", {"segment_id": segment_id, "status": seg.get("status")})
        return seg

    def get(self, segment_id: str) -> Dict[str, Any]:
        for seg in self.queue.get("segments", []):
            if seg.get("segment_id") == segment_id:
                return seg
        raise KeyError(f"segment not found: {segment_id}")

    def split(self, segment_id: str, max_length: int = 1000) -> List[Dict[str, Any]]:
        original = self.get(segment_id)
        children = split_segment(original, max_length=max_length)
        self.queue["segments"] = [seg for seg in self.queue.get("segments", []) if seg.get("segment_id") != segment_id] + children
        self.queue["segments"] = sort_segments(self.queue["segments"])
        add_queue_event(self.queue, "segment_split", {"segment_id": segment_id, "children": [c.get("segment_id") for c in children]})
        return children

    def merge(self, merge_group: str, separator: str = "") -> Dict[str, Any]:
        group_segments = [seg for seg in self.queue.get("segments", []) if seg.get("merge_group") == merge_group or seg.get("split_from") == merge_group]
        result = merge_segments(group_segments, separator=separator)
        add_queue_event(self.queue, "segment_merged", {"merge_group": merge_group, "count": result["count"]})
        return result

    def resume_from(self, completed_ids: Iterable[str]) -> Dict[str, Any]:
        done = set(completed_ids)
        for seg in self.queue.get("segments", []):
            if seg.get("segment_id") in done:
                seg["status"] = SEGMENT_COMPLETED
        add_queue_event(self.queue, "queue_resumed", {"completed": len(done)})
        return self.queue

    def metrics(self) -> Dict[str, Any]:
        return queue_metrics(self.queue)

    def manifest(self) -> Dict[str, Any]:
        return export_segment_manifest(self.queue)


class TranslationSegmentManagerAdapter:
    def __init__(self, manager: Optional[TranslationSegmentManager] = None):
        self.manager = manager or TranslationSegmentManager()

    def load(self, segments: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        return self.manager.load(segments)

    def next(self) -> Optional[Dict[str, Any]]:
        return self.manager.next()

    def start(self, segment_id: str) -> Dict[str, Any]:
        return self.manager.start(segment_id)

    def complete(self, segment_id: str, target_text: str) -> Dict[str, Any]:
        return self.manager.complete(segment_id, target_text)

    def fail(self, segment_id: str, error: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.manager.fail(segment_id, error)

    def validate(self) -> bool:
        return all(validate_managed_segment(seg) for seg in self.manager.queue.get("segments", []))

    def manifest(self) -> Dict[str, Any]:
        return self.manager.manifest()


def create_translation_segment_manager(segments: Optional[Iterable[Dict[str, Any]]] = None) -> TranslationSegmentManager:
    return TranslationSegmentManager(segments)


def create_translation_segment_manager_adapter(segments: Optional[Iterable[Dict[str, Any]]] = None) -> TranslationSegmentManagerAdapter:
    return TranslationSegmentManagerAdapter(TranslationSegmentManager(segments or []))
