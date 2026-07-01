from __future__ import annotations

from .base import StaticKnowledgeProvider


class SceneKnowledgeProvider(StaticKnowledgeProvider):
    domain = "scene"
    source = "scene_provider"


__all__ = ["SceneKnowledgeProvider"]
