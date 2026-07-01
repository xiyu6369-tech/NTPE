"""Foundation-08.8 Knowledge Import / Export manifest."""

from __future__ import annotations

from typing import Any, Dict


def build_knowledge_io_manifest(**metadata: Any) -> Dict[str, Any]:
    return {
        "name": "knowledge_import_export",
        "version": "foundation-08.8",
        "enabled": True,
        "capabilities": [
            "export_json",
            "import_json",
            "export_zip",
            "import_zip",
            "package_build",
            "package_read",
            "snapshot_package",
            "project_migration",
            "validation",
            "version_compatibility",
        ],
        "metadata": dict(metadata or {}),
    }


__all__ = ["build_knowledge_io_manifest"]
