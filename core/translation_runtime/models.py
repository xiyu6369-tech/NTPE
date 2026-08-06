"""RM-6.2.2 Translation Runtime domain models.

Immutable request/response models bridging Prompt Runtime
and Translation Engine. No provider imports. No network calls.
No Translation Engine modifications.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _deterministic_hash(*parts: str) -> str:
    """Deterministic SHA-256 hash across ordered string parts.

    Same inputs across any invocation produce the same hash.
    """
    joined = "\x00".join(parts)
    return sha256(joined.encode("utf-8")).hexdigest()


def _section_content_hash(sections: List[Dict[str, Any]]) -> str:
    """Deterministic content hash of prompt sections.

    Only hashes section name + content (not metadata). Metadata
    changes do not affect prompt identity.
    """
    payloads: List[str] = []
    for s in sections:
        name = str(s.get("name", ""))
        content = str(s.get("content", ""))
        payloads.append(f"{name}={content}")
    return _deterministic_hash(*payloads)


@dataclass(frozen=True)
class TranslationRequest:
    """Immutable translation request prepared by TranslationRuntimeAdapter.

    Carries the fully assembled prompt payload, token budget
    information, runtime metadata, and a deterministic prompt hash.
    This is the sole interface between Translation Runtime and
    Translation Engine — the Engine never sees the internal
    prompt assembly pipeline.
    """

    prompt: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    runtime_snapshot: Dict[str, Any] = field(default_factory=dict)

    snapshot_id: str = ""
    prompt_hash: str = ""
    section_count: int = 0
    token_count: int = 0
    build_timestamp: str = field(default_factory=utc_now_iso)

    version: str = "rm-6.2.2"

    @property
    def id(self) -> str:
        return self.snapshot_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt": self.prompt,
            "metadata": dict(self.metadata),
            "runtime_snapshot": dict(self.runtime_snapshot),
            "snapshot_id": self.snapshot_id,
            "prompt_hash": self.prompt_hash,
            "section_count": self.section_count,
            "token_count": self.token_count,
            "build_timestamp": self.build_timestamp,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TranslationRequest":
        return cls(
            prompt=str(payload.get("prompt", "")),
            metadata=dict(payload.get("metadata") or {}),
            runtime_snapshot=dict(payload.get("runtime_snapshot") or {}),
            snapshot_id=str(payload.get("snapshot_id", "")),
            prompt_hash=str(payload.get("prompt_hash", "")),
            section_count=int(payload.get("section_count", 0)),
            token_count=int(payload.get("token_count", 0)),
            build_timestamp=str(payload.get("build_timestamp") or utc_now_iso()),
            version=str(payload.get("version", "rm-6.2.2")),
        )


@dataclass(frozen=True)
class TranslationResponse:
    """Immutable translation response from the Translation Engine.

    Currently a placeholder that wraps the request without calling
    any provider. Expands in later RM-6.x phases.
    """

    prompt: str
    request: TranslationRequest

    version: str = "rm-6.2.2"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt": self.prompt,
            "request": self.request.to_dict(),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TranslationResponse":
        req = TranslationRequest.from_dict(payload["request"])
        return cls(
            prompt=str(payload.get("prompt", "")),
            request=req,
            version=str(payload.get("version", "rm-6.2.2")),
        )


__all__ = [
    "TranslationRequest",
    "TranslationResponse",
    "utc_now_iso",
]