"""Foundation-08.7 Knowledge Snapshot serializer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from ..contracts import KnowledgeSnapshot


class KnowledgeSnapshotSerializer:
    """Serialize and deserialize KnowledgeSnapshot payloads.

    The serializer stays dependency-free and dictionary based so future storage
    backends can reuse it without binding the Snapshot Manager to JSON files.
    """

    version = "foundation-08.7"

    def to_dict(self, snapshot: KnowledgeSnapshot | Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(snapshot, KnowledgeSnapshot):
            payload = snapshot.to_dict()
        else:
            payload = dict(snapshot or {})
        payload.setdefault("version", self.version)
        payload.setdefault("metadata", {})
        payload["metadata"] = dict(payload.get("metadata") or {})
        payload["metadata"].setdefault("serializer", self.version)
        return payload

    def from_dict(self, payload: Dict[str, Any]) -> KnowledgeSnapshot:
        return KnowledgeSnapshot.from_dict(dict(payload or {}))

    def dumps(self, snapshot: KnowledgeSnapshot | Dict[str, Any], **kwargs: Any) -> str:
        options = {"ensure_ascii": False, "indent": 2}
        options.update(kwargs)
        return json.dumps(self.to_dict(snapshot), **options)

    def loads(self, text: str) -> KnowledgeSnapshot:
        return self.from_dict(json.loads(text))

    def save(self, snapshot: KnowledgeSnapshot | Dict[str, Any], path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.dumps(snapshot), encoding="utf-8")
        return output_path

    def load(self, path: str | Path) -> KnowledgeSnapshot:
        return self.loads(Path(path).read_text(encoding="utf-8"))


__all__ = ["KnowledgeSnapshotSerializer"]
