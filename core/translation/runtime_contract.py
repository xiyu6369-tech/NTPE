"""
NTPE Foundation-06.0 Translation Runtime Contract

Incremental module that defines the first stable translation runtime contract.
It is intentionally dependency-light and backward-compatible with the existing
Foundation-05 Production Runtime by using dictionary payloads and soft adapters.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Iterable, List, Optional
import time
import uuid


TRANSLATION_CONTRACT_VERSION = "06.0"


@dataclass
class TranslationSegment:
    segment_id: str
    index: int
    source_text: str
    status: str = "pending"
    translated_text: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TranslationJob:
    job_id: str
    source_language: str = "ko"
    target_language: str = "zh-TW"
    status: str = "created"
    segments: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TranslationContext:
    job_id: str
    target_language: str = "zh-TW"
    glossary: Dict[str, str] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=dict)
    previous_segments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TranslationError:
    error_id: str
    code: str
    message: str
    stage: str = "translation"
    retryable: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TranslationResult:
    ok: bool
    status: str
    job_id: str
    output_text: str = ""
    segments: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TranslationManifest:
    name: str = "NTPE Translation Runtime Contract"
    version: str = TRANSLATION_CONTRACT_VERSION
    contract: str = "translation-runtime"
    capabilities: List[str] = field(default_factory=lambda: [
        "translation_job",
        "translation_segment",
        "translation_context",
        "translation_result",
        "translation_error",
        "production_runtime_payload",
    ])
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def create_translation_segment(
    source_text: str,
    *,
    index: int = 0,
    segment_id: Optional[str] = None,
    status: str = "pending",
    translated_text: str = "",
    context: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    return TranslationSegment(
        segment_id=segment_id or _new_id("segment"),
        index=index,
        source_text=source_text or "",
        status=status,
        translated_text=translated_text or "",
        context=context or {},
        metadata=metadata or {},
        error=error,
    ).to_dict()


def normalize_translation_segment(segment: Any, *, index: int = 0) -> Dict[str, Any]:
    if isinstance(segment, str):
        return create_translation_segment(segment, index=index)
    if not isinstance(segment, dict):
        return create_translation_segment(str(segment), index=index)
    normalized = dict(segment)
    normalized.setdefault("segment_id", _new_id("segment"))
    normalized.setdefault("index", index)
    normalized.setdefault("source_text", normalized.get("source", ""))
    normalized.setdefault("translated_text", "")
    normalized.setdefault("status", "pending")
    normalized.setdefault("context", {})
    normalized.setdefault("metadata", {})
    normalized.setdefault("error", None)
    return normalized


def validate_translation_segment(segment: Dict[str, Any]) -> bool:
    if not isinstance(segment, dict):
        return False
    if not segment.get("segment_id"):
        return False
    if not isinstance(segment.get("index"), int):
        return False
    if "source_text" not in segment:
        return False
    if segment.get("status") not in {"pending", "running", "completed", "failed", "skipped"}:
        return False
    return True


def create_translation_job(
    source: Any = "",
    *,
    job_id: Optional[str] = None,
    source_language: str = "ko",
    target_language: str = "zh-TW",
    segments: Optional[Iterable[Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if segments is None:
        if isinstance(source, list):
            raw_segments = source
        else:
            raw_segments = [source]
    else:
        raw_segments = list(segments)
    normalized_segments = [normalize_translation_segment(item, index=i) for i, item in enumerate(raw_segments)]
    return TranslationJob(
        job_id=job_id or _new_id("job"),
        source_language=source_language,
        target_language=target_language,
        segments=normalized_segments,
        context=context or {},
        metadata=metadata or {},
    ).to_dict()


def normalize_translation_job(job: Any) -> Dict[str, Any]:
    if isinstance(job, dict) and "segments" in job:
        normalized = dict(job)
        normalized.setdefault("job_id", _new_id("job"))
        normalized.setdefault("source_language", "ko")
        normalized.setdefault("target_language", "zh-TW")
        normalized.setdefault("status", "created")
        normalized.setdefault("context", {})
        normalized.setdefault("metadata", {})
        normalized.setdefault("created_at", time.time())
        normalized["segments"] = [normalize_translation_segment(s, index=i) for i, s in enumerate(normalized.get("segments", []))]
        return normalized
    if isinstance(job, dict):
        return create_translation_job(job.get("source", ""), target_language=job.get("target_language", "zh-TW"), context=job.get("context", {}), metadata=job.get("metadata", {}))
    return create_translation_job(job)


def validate_translation_job(job: Dict[str, Any]) -> bool:
    if not isinstance(job, dict):
        return False
    if not job.get("job_id"):
        return False
    if not job.get("target_language"):
        return False
    if not isinstance(job.get("segments"), list):
        return False
    return all(validate_translation_segment(segment) for segment in job.get("segments", []))


def create_translation_context(job: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
    normalized = normalize_translation_job(job)
    return TranslationContext(
        job_id=normalized["job_id"],
        target_language=normalized.get("target_language", "zh-TW"),
        glossary=kwargs.get("glossary", normalized.get("context", {}).get("glossary", {})),
        memory=kwargs.get("memory", normalized.get("context", {}).get("memory", {})),
        previous_segments=kwargs.get("previous_segments", []),
        metadata=kwargs.get("metadata", {}),
    ).to_dict()


def validate_translation_context(context: Dict[str, Any]) -> bool:
    return isinstance(context, dict) and bool(context.get("job_id")) and bool(context.get("target_language"))


def create_translation_error(code: str, message: str, **kwargs: Any) -> Dict[str, Any]:
    return TranslationError(
        error_id=kwargs.get("error_id") or _new_id("error"),
        code=code,
        message=message,
        stage=kwargs.get("stage", "translation"),
        retryable=kwargs.get("retryable", True),
        metadata=kwargs.get("metadata", {}),
    ).to_dict()


def validate_translation_error(error: Dict[str, Any]) -> bool:
    return isinstance(error, dict) and bool(error.get("error_id")) and bool(error.get("code"))


def create_translation_result(
    job: Dict[str, Any],
    *,
    ok: bool = True,
    status: str = "completed",
    segments: Optional[List[Dict[str, Any]]] = None,
    errors: Optional[List[Dict[str, Any]]] = None,
    context: Optional[Dict[str, Any]] = None,
    metrics: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    normalized = normalize_translation_job(job)
    result_segments = segments if segments is not None else normalized.get("segments", [])
    output_text = "\n".join(s.get("translated_text") or s.get("source_text", "") for s in result_segments)
    return TranslationResult(
        ok=ok,
        status=status,
        job_id=normalized["job_id"],
        output_text=output_text,
        segments=result_segments,
        context=context or normalized.get("context", {}),
        metrics=metrics or {},
        errors=errors or [],
        metadata=metadata or {},
    ).to_dict()


def validate_translation_result(result: Dict[str, Any]) -> bool:
    if not isinstance(result, dict):
        return False
    if not result.get("job_id"):
        return False
    if result.get("status") not in {"completed", "failed", "partial", "aborted"}:
        return False
    if not isinstance(result.get("segments"), list):
        return False
    return True


def create_translation_manifest(**metadata: Any) -> Dict[str, Any]:
    return TranslationManifest(metadata=metadata).to_dict()


def validate_translation_manifest(manifest: Dict[str, Any]) -> bool:
    return isinstance(manifest, dict) and manifest.get("contract") == "translation-runtime" and bool(manifest.get("version"))


def build_production_runtime_payload(job: Dict[str, Any]) -> Dict[str, Any]:
    normalized = normalize_translation_job(job)
    source = "\n".join(segment.get("source_text", "") for segment in normalized.get("segments", []))
    return {
        "source": source,
        "context": normalized.get("context", {}),
        "metadata": {
            **normalized.get("metadata", {}),
            "translation_job": normalized,
            "contract": "translation-runtime",
            "contract_version": TRANSLATION_CONTRACT_VERSION,
        },
    }


class TranslationRuntimeContractAdapter:
    """Adapter that lets Foundation-05 Production Runtime consume Translation Jobs."""

    def __init__(self, manifest: Optional[Dict[str, Any]] = None) -> None:
        self._manifest = manifest or create_translation_manifest(adapter="translation-runtime-contract")

    def normalize_job(self, job: Any) -> Dict[str, Any]:
        return normalize_translation_job(job)

    def validate_job(self, job: Dict[str, Any]) -> bool:
        return validate_translation_job(job)

    def build_payload(self, job: Dict[str, Any]) -> Dict[str, Any]:
        return build_production_runtime_payload(job)

    def create_context(self, job: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        return create_translation_context(job, **kwargs)

    def create_result(self, job: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        return create_translation_result(job, **kwargs)

    def manifest(self) -> Dict[str, Any]:
        return dict(self._manifest)

    def validate(self) -> bool:
        return validate_translation_manifest(self._manifest)


# Backward-compatible aliases for future import stability.
create_job = create_translation_job
create_segment = create_translation_segment
create_context = create_translation_context
create_result = create_translation_result
create_error = create_translation_error
create_manifest = create_translation_manifest
