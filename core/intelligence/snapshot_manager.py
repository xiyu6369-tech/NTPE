"""Foundation-07.3 Intelligence snapshot manager."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional

from .merge_strategy import IntelligenceMergeStrategy
from .session_scope import IntelligenceSessionScope
from .versioning import SnapshotVersion, utc_now_iso


class IntelligenceSnapshotManager:
    """Creates, versions, merges, and prunes intelligence snapshots."""

    version = "foundation-07.3"

    def __init__(self, merge_strategy: Optional[IntelligenceMergeStrategy] = None) -> None:
        self.merge_strategy = merge_strategy or IntelligenceMergeStrategy()
        self._history: List[Dict[str, Any]] = []

    def create_snapshot(
        self,
        data: Optional[Dict[str, Any]] = None,
        scope: Optional[IntelligenceSessionScope] = None,
        version: Optional[SnapshotVersion] = None,
    ) -> Dict[str, Any]:
        base = deepcopy(data or {})
        scope = scope or IntelligenceSessionScope()
        version = version or SnapshotVersion(version_id=f"snapshot-{len(self._history) + 1}")

        manifest = dict(base.get("manifest", {}))
        manifest.update(
            {
                "component": "translation_intelligence_lifecycle",
                "foundation": "07.3",
                "lifecycle_version": self.version,
                "created_at": utc_now_iso(),
                "scope": scope.to_dict(),
                "version": version.to_dict(),
            }
        )
        base["manifest"] = manifest
        self._history.append(deepcopy(base))
        return base

    def bump_snapshot(self, snapshot: Dict[str, Any], version_id: Optional[str] = None) -> Dict[str, Any]:
        current_manifest = dict(snapshot.get("manifest", {}))
        current_version = SnapshotVersion.from_dict(current_manifest.get("version", {}))
        next_version = current_version.bump(version_id=version_id)
        return self.create_snapshot(snapshot, scope=IntelligenceSessionScope.from_dict(current_manifest.get("scope", {})), version=next_version)

    def merge_snapshots(self, *snapshots: Dict[str, Any], scope: Optional[IntelligenceSessionScope] = None) -> Dict[str, Any]:
        merged = self.merge_strategy.merge_many(snapshots)
        return self.create_snapshot(merged, scope=scope)

    def latest(self) -> Optional[Dict[str, Any]]:
        return deepcopy(self._history[-1]) if self._history else None

    def history(self) -> List[Dict[str, Any]]:
        return deepcopy(self._history)

    def cleanup(self, keep_last: int = 10) -> Dict[str, Any]:
        if keep_last < 0:
            keep_last = 0
        removed = max(0, len(self._history) - keep_last)
        if removed:
            self._history = self._history[-keep_last:] if keep_last else []
        return {"removed": removed, "remaining": len(self._history)}
