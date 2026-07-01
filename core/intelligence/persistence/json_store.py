"""Foundation-07.4 JSON persistence store."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..persistence_contract import IntelligencePersistenceContract
from .serializer import IntelligenceSnapshotSerializer


class JsonIntelligenceStore(IntelligencePersistenceContract):
    """File-per-scope JSON implementation of the intelligence persistence contract."""

    version = "foundation-07.4"

    def __init__(self, root_dir: str = "ntpe_intelligence_store", serializer: Optional[IntelligenceSnapshotSerializer] = None) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.serializer = serializer or IntelligenceSnapshotSerializer()

    def _safe_name(self, scope_key: str) -> str:
        safe = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in str(scope_key))
        return safe or "default"

    def _path(self, scope_key: str) -> Path:
        return self.root_dir / f"{self._safe_name(scope_key)}.json"

    def save_snapshot(self, scope_key: str, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        data = self.serializer.normalize(snapshot)
        path = self._path(scope_key)
        temp_path = path.with_suffix(".json.tmp")
        temp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(temp_path, path)
        return self.load_snapshot(scope_key) or data

    def load_snapshot(self, scope_key: str) -> Optional[Dict[str, Any]]:
        path = self._path(scope_key)
        if not path.exists():
            return None
        return self.serializer.loads(path.read_text(encoding="utf-8"))

    def list_scope_keys(self) -> List[str]:
        keys: List[str] = []
        for path in sorted(self.root_dir.glob("*.json")):
            keys.append(path.stem)
        return keys

    def delete_snapshot(self, scope_key: str) -> bool:
        path = self._path(scope_key)
        if not path.exists():
            return False
        path.unlink()
        return True
