from __future__ import annotations

from .base import StaticKnowledgeProvider


class GlossaryKnowledgeProvider(StaticKnowledgeProvider):
    domain = "glossary"
    source = "glossary_provider"


__all__ = ["GlossaryKnowledgeProvider"]
