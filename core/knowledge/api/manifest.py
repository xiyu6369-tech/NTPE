"""Foundation-08.5 Knowledge Query API manifest."""

from __future__ import annotations

from typing import Any, Dict, Optional


def build_knowledge_api_manifest(metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "name": "knowledge_query_api",
        "version": "foundation-08.5",
        "enabled": True,
        "capabilities": [
            "query_api",
            "query_builder",
            "query_executor",
            "filter",
            "sort",
            "pagination",
            "runtime_query",
            "prompt_query",
            "plugin_query",
            "cache_aware_query",
            "snapshot_query",
        ],
        "metadata": dict(metadata or {}),
    }


__all__ = ["build_knowledge_api_manifest"]
