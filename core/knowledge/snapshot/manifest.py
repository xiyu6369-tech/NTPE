"""Foundation-08.7 Knowledge Snapshot Manager manifest."""

from __future__ import annotations

from typing import Any, Dict


def build_knowledge_snapshot_manifest(**metadata: Any) -> Dict[str, Any]:
    base_metadata: Dict[str, Any] = {
        "foundation": "08.7",
        "layer": "knowledge_snapshot_manager",
    }
    base_metadata.update(dict(metadata or {}))
    return {
        "name": "knowledge_snapshot_manager",
        "version": "foundation-08.7",
        "enabled": True,
        "capabilities": [
            "snapshot_manager",
            "snapshot_registry",
            "snapshot_history",
            "snapshot_diff",
            "snapshot_merge",
            "snapshot_rollback",
            "snapshot_export",
            "snapshot_import",
            "runtime_snapshot_control",
            "event_bus_snapshot",
        ],
        "metadata": base_metadata,
    }


__all__ = ["build_knowledge_snapshot_manifest"]
