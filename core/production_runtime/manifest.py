"""NTPE 1.0 Beta Stage-01 Production Runtime manifest."""
from __future__ import annotations

from typing import Any, Dict, Optional

VERSION = "ntpe-1.0-beta-stage-01"


def build_production_runtime_manifest(metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "name": "ntpe_production_runtime",
        "version": VERSION,
        "stage": "NTPE 1.0 Beta Stage-01",
        "components": [
            "RuntimeHost",
            "RuntimeScheduler",
            "RuntimeSessionManager",
            "RuntimeCheckpointStore",
            "RuntimeRecoveryManager",
            "RuntimeMetrics",
            "RuntimeTelemetry",
        ],
        "capabilities": [
            "production_host",
            "job_scheduler",
            "session_lock",
            "checkpoint",
            "resume",
            "recovery",
            "metrics",
            "telemetry",
            "knowledge_runtime_bridge",
        ],
        "metadata": dict(metadata or {}),
    }


__all__ = ["VERSION", "build_production_runtime_manifest"]
