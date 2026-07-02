"""Stage-08.0 Integration Core manifest.

This module is additive and does not modify frozen Foundation, CLI, Runtime, or
SDK contracts. It records integration-layer capabilities for regression tests
and future Stage-08 extension work.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

INTEGRATION_VERSION = "0.8.0"
INTEGRATION_STAGE = "NTPE 1.0 Beta Stage-08.0 Integration Core"
FOUNDATION_STATUS = "frozen"


def build_integration_manifest(metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "name": "ntpe-integration-core",
        "version": INTEGRATION_VERSION,
        "stage": INTEGRATION_STAGE,
        "foundation_status": FOUNDATION_STATUS,
        "compatibility": {
            "foundation_v1": True,
            "cli_freeze": True,
            "sdk_stage_07": True,
            "runtime_shared": True,
            "additive_only": True,
        },
        "components": ["runtime", "cli", "sdk", "plugin", "extension"],
        "metadata": dict(metadata or {}),
    }
