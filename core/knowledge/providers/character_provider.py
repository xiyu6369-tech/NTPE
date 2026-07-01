from __future__ import annotations

from .base import StaticKnowledgeProvider


class CharacterKnowledgeProvider(StaticKnowledgeProvider):
    domain = "character"
    source = "character_provider"


__all__ = ["CharacterKnowledgeProvider"]
