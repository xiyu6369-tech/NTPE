"""Foundation-07.4 Intelligence persistence serializer."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict


class IntelligenceSnapshotSerializer:
    """Serialize and normalize intelligence snapshots for durable stores."""

    version = "foundation-07.4"

    def normalize(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        data = deepcopy(snapshot or {})
        manifest = dict(data.get("manifest", {}))
        manifest.setdefault("component", "translation_intelligence_persistence")
        manifest.setdefault("foundation", "07.4")
        manifest.setdefault("persistence_version", self.version)
        manifest.setdefault("serialized_at", datetime.now(timezone.utc).isoformat())
        data["manifest"] = manifest
        return data

    def dumps(self, snapshot: Dict[str, Any]) -> str:
        return json.dumps(self.normalize(snapshot), ensure_ascii=False, sort_keys=True)

    def loads(self, payload: str) -> Dict[str, Any]:
        data = json.loads(payload or "{}")
        if not isinstance(data, dict):
            raise ValueError("snapshot payload must decode to a dictionary")
        return data

    def clone(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        return self.loads(self.dumps(snapshot))
