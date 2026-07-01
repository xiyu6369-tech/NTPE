"""Foundation-08.0 Knowledge manifest exports."""

from __future__ import annotations

from .contracts import KnowledgeManifest


def build_knowledge_manifest(**metadata) -> KnowledgeManifest:
    return KnowledgeManifest(metadata=dict(metadata))


__all__ = ["KnowledgeManifest", "build_knowledge_manifest"]
