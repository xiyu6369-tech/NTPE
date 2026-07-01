"""Foundation-08.2 Knowledge Runtime manifest helpers."""

from __future__ import annotations

from typing import Any, Dict, Optional


def build_knowledge_runtime_manifest(metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return a runtime-safe manifest for the Knowledge Runtime layer."""

    return {
        "name": "knowledge_runtime",
        "version": "foundation-08.2",
        "enabled": True,
        "capabilities": [
            "context_runtime",
            "prompt_runtime",
            "repository_runtime",
            "session_runtime",
            "runtime_snapshot",
        ],
        "metadata": dict(metadata or {}),
    }


__all__ = ["build_knowledge_runtime_manifest"]
