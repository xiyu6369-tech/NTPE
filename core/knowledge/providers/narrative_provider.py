from __future__ import annotations

from .base import StaticKnowledgeProvider


class NarrativeKnowledgeProvider(StaticKnowledgeProvider):
    domain = "narrative"
    source = "narrative_provider"


__all__ = ["NarrativeKnowledgeProvider"]
