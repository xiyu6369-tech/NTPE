"""Foundation-08.0 Knowledge query API."""

from __future__ import annotations

from .contracts import KnowledgeQuery


def build_query(text: str = "", domain: str | None = None, limit: int | None = None, **metadata) -> KnowledgeQuery:
    """Small helper used by tests/runtime callers to construct a query safely."""

    return KnowledgeQuery(text=text, domain=domain, limit=limit, metadata=dict(metadata))


__all__ = ["KnowledgeQuery", "build_query"]
