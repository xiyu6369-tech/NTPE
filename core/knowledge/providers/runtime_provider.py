"""Runtime-facing Knowledge Provider."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..contracts import KnowledgeQuery
from ..provider import RepositoryKnowledgeProvider
from ..repositories.memory_repository import KnowledgeMemoryRepository


class RuntimeKnowledgeProvider(RepositoryKnowledgeProvider):
    """Provider facade used by Runtime and Prompt Pipeline."""

    def __init__(self, repository: Optional[KnowledgeMemoryRepository] = None):
        super().__init__(repository or KnowledgeMemoryRepository())

    def attach_to_runtime_payload(self, payload: Optional[Dict[str, Any]] = None, query: Optional[KnowledgeQuery] = None) -> Dict[str, Any]:
        next_payload = dict(payload or {})
        next_payload["knowledge"] = self.build_context(query)
        return next_payload


__all__ = ["RuntimeKnowledgeProvider"]
