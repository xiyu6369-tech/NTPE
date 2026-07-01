"""NTPE Foundation-06.3 Translation Context Runtime.

Builds versioned context bundles for translation segments. The module is
incremental and dictionary-compatible: existing segment/job/context dictionaries
are copied and normalized without destructive mutation.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = "Foundation-06.3"
CONTEXT_TYPE = "translation_context_bundle"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _segment_id(segment: Dict[str, Any]) -> str:
    return str(segment.get("segment_id") or segment.get("id") or f"segment-{segment.get('index', 0)}")


def _segment_index(segment: Dict[str, Any]) -> int:
    try:
        return int(segment.get("index", 0))
    except Exception:
        return 0


def normalize_glossary(glossary: Any) -> Dict[str, str]:
    if glossary is None:
        return {}
    if isinstance(glossary, dict):
        return {str(k): str(v) for k, v in glossary.items()}
    if isinstance(glossary, list):
        result: Dict[str, str] = {}
        for item in glossary:
            if isinstance(item, dict):
                source = item.get("source") or item.get("term") or item.get("from")
                target = item.get("target") or item.get("translation") or item.get("to")
                if source is not None and target is not None:
                    result[str(source)] = str(target)
        return result
    return {}


def create_context_bundle(
    segment: Dict[str, Any],
    job: Optional[Dict[str, Any]] = None,
    previous_segments: Optional[Iterable[Dict[str, Any]]] = None,
    next_segments: Optional[Iterable[Dict[str, Any]]] = None,
    glossary: Optional[Any] = None,
    character_context: Optional[Dict[str, Any]] = None,
    narrative_context: Optional[Dict[str, Any]] = None,
    scene_context: Optional[Dict[str, Any]] = None,
    user_metadata: Optional[Dict[str, Any]] = None,
    pipeline_context: Optional[Dict[str, Any]] = None,
    version: int = 1,
) -> Dict[str, Any]:
    seg = deepcopy(segment or {})
    job_data = deepcopy(job or {})
    previous = [deepcopy(s) for s in (previous_segments or [])]
    upcoming = [deepcopy(s) for s in (next_segments or [])]
    job_glossary = job_data.get("glossary") or job_data.get("context", {}).get("glossary")
    bundle = {
        "type": CONTEXT_TYPE,
        "version": int(version),
        "context_id": f"context::{job_data.get('job_id', 'job')}::{_segment_id(seg)}::v{int(version)}",
        "created_at": _now(),
        "segment": {
            "segment_id": _segment_id(seg),
            "index": _segment_index(seg),
            "source_text": seg.get("source_text", seg.get("text", "")),
            "metadata": deepcopy(seg.get("metadata", {})),
        },
        "job": {
            "job_id": job_data.get("job_id", job_data.get("id", "job")),
            "source_language": job_data.get("source_language", "auto"),
            "target_language": job_data.get("target_language", job_data.get("target", "zh-TW")),
            "metadata": deepcopy(job_data.get("metadata", {})),
        },
        "previous_context": [compact_segment_context(s) for s in previous],
        "next_context": [compact_segment_context(s) for s in upcoming],
        "glossary_context": normalize_glossary(glossary if glossary is not None else job_glossary),
        "character_context": deepcopy(character_context or job_data.get("character_context", {})),
        "narrative_context": deepcopy(narrative_context or job_data.get("narrative_context", {})),
        "scene_context": deepcopy(scene_context or seg.get("scene_context", {})),
        "runtime_metadata": {"runtime": "translation_context_runtime", "foundation": VERSION},
        "user_metadata": deepcopy(user_metadata or job_data.get("user_metadata", {})),
        "pipeline_context": deepcopy(pipeline_context or job_data.get("pipeline_context", {})),
    }
    return bundle


def compact_segment_context(segment: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "segment_id": _segment_id(segment),
        "index": _segment_index(segment),
        "source_text": segment.get("source_text", segment.get("text", "")),
        "target_text": segment.get("target_text", segment.get("output", "")),
        "status": segment.get("status", "pending"),
        "metadata": deepcopy(segment.get("metadata", {})),
    }


def validate_context_bundle(bundle: Dict[str, Any]) -> bool:
    if not isinstance(bundle, dict):
        return False
    if bundle.get("type") != CONTEXT_TYPE:
        return False
    if not bundle.get("context_id"):
        return False
    if not isinstance(bundle.get("version"), int):
        return False
    for key in ["segment", "job", "previous_context", "next_context", "glossary_context", "runtime_metadata"]:
        if key not in bundle:
            return False
    if not bundle["segment"].get("segment_id"):
        return False
    return True


def context_cache_key(job_id: str, segment_id: str, version: int = 1) -> str:
    return f"{job_id}:{segment_id}:v{int(version)}"


class TranslationContextCache:
    def __init__(self) -> None:
        self._items: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        item = self._items.get(key)
        return deepcopy(item) if item is not None else None

    def set(self, key: str, bundle: Dict[str, Any]) -> Dict[str, Any]:
        self._items[key] = deepcopy(bundle)
        return deepcopy(bundle)

    def has(self, key: str) -> bool:
        return key in self._items

    def clear(self) -> None:
        self._items.clear()

    def manifest(self) -> Dict[str, Any]:
        return {"type": "translation_context_cache", "count": len(self._items), "keys": sorted(self._items.keys())}


class TranslationContextBuilder:
    def __init__(self, job: Optional[Dict[str, Any]] = None, cache: Optional[TranslationContextCache] = None, window: int = 1) -> None:
        self.job = deepcopy(job or {})
        self.cache = cache or TranslationContextCache()
        self.window = max(int(window), 0)
        self.events: List[Dict[str, Any]] = []

    def _event(self, event: str, **data: Any) -> None:
        self.events.append({"event": event, "timestamp": _now(), **data})

    def build(self, segment: Dict[str, Any], segments: Optional[Iterable[Dict[str, Any]]] = None, version: int = 1, use_cache: bool = True, **kwargs: Any) -> Dict[str, Any]:
        seg_id = _segment_id(segment)
        job_id = str(self.job.get("job_id", self.job.get("id", "job")))
        key = context_cache_key(job_id, seg_id, version)
        if use_cache and self.cache.has(key):
            self._event("context_cache_hit", context_id=key, segment_id=seg_id)
            return self.cache.get(key) or {}

        ordered = sorted([deepcopy(s) for s in (segments or [])], key=_segment_index)
        idx = _segment_index(segment)
        previous = [s for s in ordered if _segment_index(s) < idx][-self.window :]
        upcoming = [s for s in ordered if _segment_index(s) > idx][: self.window]
        bundle = create_context_bundle(
            segment=segment,
            job=self.job,
            previous_segments=previous,
            next_segments=upcoming,
            glossary=kwargs.get("glossary"),
            character_context=kwargs.get("character_context"),
            narrative_context=kwargs.get("narrative_context"),
            scene_context=kwargs.get("scene_context"),
            user_metadata=kwargs.get("user_metadata"),
            pipeline_context=kwargs.get("pipeline_context"),
            version=version,
        )
        self.cache.set(key, bundle)
        self._event("context_built", context_id=bundle["context_id"], segment_id=seg_id)
        return bundle

    def manifest(self) -> Dict[str, Any]:
        return create_context_manifest(events=self.events, cache=self.cache.manifest())


def create_context_manifest(events: Optional[List[Dict[str, Any]]] = None, cache: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "name": "NTPE Foundation-06.3 Translation Context Runtime",
        "version": VERSION,
        "type": "translation_context_runtime",
        "capabilities": [
            "context_bundle",
            "previous_context",
            "next_context",
            "glossary_context",
            "character_context",
            "narrative_context",
            "scene_context",
            "context_cache",
            "context_version",
            "runtime_context_adapter",
        ],
        "events": deepcopy(events or []),
        "cache": deepcopy(cache or {}),
        "compatible_with": ["Foundation-06.2", "Foundation-06.1", "Foundation-06.0", "Foundation-05.6"],
    }


class TranslationContextRuntimeAdapter:
    def __init__(self, builder: Optional[TranslationContextBuilder] = None) -> None:
        self.builder = builder or TranslationContextBuilder()

    def build_context(self, segment: Dict[str, Any], segments: Optional[Iterable[Dict[str, Any]]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self.builder.build(segment, segments, **kwargs)

    def attach_context(self, payload: Dict[str, Any], segment: Dict[str, Any], segments: Optional[Iterable[Dict[str, Any]]] = None, **kwargs: Any) -> Dict[str, Any]:
        data = deepcopy(payload or {})
        data["translation_context"] = self.build_context(segment, segments, **kwargs)
        return data

    def validate(self, bundle: Dict[str, Any]) -> bool:
        return validate_context_bundle(bundle)

    def manifest(self) -> Dict[str, Any]:
        return self.builder.manifest()


def create_translation_context_runtime_adapter(job: Optional[Dict[str, Any]] = None, window: int = 1) -> TranslationContextRuntimeAdapter:
    return TranslationContextRuntimeAdapter(TranslationContextBuilder(job=job, window=window))
