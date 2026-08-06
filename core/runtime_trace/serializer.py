"""RM-6.3.3 Runtime Trace Serialization.

Serializes and deserializes trace metadata to/from dict and JSON.
Only trace metadata is included in output. Prompt content,
translated text, provider responses, and API payloads are strictly
forbidden from serialization. No provider imports. No network calls.
"""

from __future__ import annotations

from dataclasses import asdict
import json
from typing import Any, Dict, List, Optional

from .models import (
    EventType,
    ChunkStatus,
    ErrorSeverity,
    TraceEvent,
    ChunkTrace,
    RetryRecord,
    CheckpointRecord,
    ErrorRecord,
)
from .timeline import RuntimeTimeline


def _serialize_event(event: TraceEvent) -> Dict[str, Any]:
    return {
        "event_id": event.event_id,
        "session_id": event.session_id,
        "chunk_index": event.chunk_index,
        "event_type": event.event_type.value,
        "timestamp": event.timestamp,
        "metadata": dict(event.metadata),
    }


def _deserialize_event(data: Dict[str, Any]) -> TraceEvent:
    return TraceEvent(
        event_id=data.get("event_id", ""),
        session_id=data.get("session_id", ""),
        chunk_index=data.get("chunk_index", 0),
        event_type=EventType(data.get("event_type", "SESSION_CREATED")),
        timestamp=data.get("timestamp", ""),
        metadata=data.get("metadata", {}),
    )



def _serialize_chunk(chunk: ChunkTrace) -> Dict[str, Any]:
    return {
        "chunk_index": chunk.chunk_index,
        "session_id": chunk.session_id,
        "started_at": chunk.started_at,
        "finished_at": chunk.finished_at,
        "duration_ms": chunk.duration_ms,
        "status": chunk.status.value,
        "retry_count": chunk.retry_count,
        "checkpoint_id": chunk.checkpoint_id,
        "metadata": dict(chunk.metadata),
    }


def _serialize_retry(retry: RetryRecord) -> Dict[str, Any]:
    return {
        "chunk_index": retry.chunk_index,
        "attempt": retry.attempt,
        "error_message": retry.error_message,
        "started_at": retry.started_at,
        "finished_at": retry.finished_at,
        "successful": retry.successful,
    }


def _serialize_checkpoint(checkpoint: CheckpointRecord) -> Dict[str, Any]:
    return {
        "checkpoint_id": checkpoint.checkpoint_id,
        "chunk_index": checkpoint.chunk_index,
        "session_id": checkpoint.session_id,
        "action": checkpoint.action,
        "snapshot_id": checkpoint.snapshot_id,
        "timestamp": checkpoint.timestamp,
    }


def _serialize_error(error: ErrorRecord) -> Dict[str, Any]:
    return {
        "chunk_index": error.chunk_index,
        "session_id": error.session_id,
        "error_type": error.error_type,
        "severity": error.severity.value,
        "error_message": error.error_message,
        "timestamp": error.timestamp,
        "metadata": dict(error.metadata),
    }


def to_dict(timeline: RuntimeTimeline) -> Dict[str, Any]:
    """Serialize a RuntimeTimeline to a plain dict.

    Only trace metadata is included. Prompt, translation, provider
    response, and API payload are NOT serialized.
    """
    return {
        "session_id": timeline.session_id,
        "version": timeline.version,
        "event_count": timeline.event_count,
        "events": [_serialize_event(e) for e in timeline.events],
    }


def to_json(timeline: RuntimeTimeline, *, indent: int | None = 2) -> str:
    """Serialize a RuntimeTimeline to a JSON string.

    Output is deterministic for a given timeline. Only trace metadata
    is included.
    """
    return json.dumps(to_dict(timeline), indent=indent, ensure_ascii=False, sort_keys=True, check_circular=True)


def from_dict(data: Dict[str, Any]) -> RuntimeTimeline:
    """Deserialize a dict into a new RuntimeTimeline.

    Only trace metadata fields are consumed. Any fields outside the
    trace contract are silently ignored.
    """
    session_id = data.get("session_id", "")
    events = [
        _deserialize_event(e)
        for e in data.get("events", [])
    ]
    return RuntimeTimeline(session_id=session_id, events=events,)


def from_json(json_str: str) -> RuntimeTimeline:
    """Deserialize a JSON string into a new RuntimeTimeline.

    Only trace metadata fields are consumed. Unknown keys in the
    JSON are silently ignored.
    """
    data = json.loads(json_str)
    return from_dict(data)


def serialize_chunk(chunk: ChunkTrace) -> Dict[str, Any]:
    return _serialize_chunk(chunk)


def serialize_retry(retry: RetryRecord) -> Dict[str, Any]:
    return _serialize_retry(retry)


def serialize_checkpoint(checkpoint: CheckpointRecord) -> Dict[str, Any]:
    return _serialize_checkpoint(checkpoint)


def serialize_error(error: ErrorRecord) -> Dict[str, Any]:
    return _serialize_error(error)


__all__ = [
    "to_dict",
    "to_json",
    "from_dict",
    "from_json",
    "serialize_chunk",
    "serialize_retry",
    "serialize_checkpoint",
    "serialize_error",
]