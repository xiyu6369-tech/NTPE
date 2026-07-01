"""Foundation-07.3 Translation Intelligence Lifecycle."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .engine import TranslationIntelligenceEngine
from .persistence_contract import InMemoryIntelligencePersistence, IntelligencePersistenceContract
from .session_scope import IntelligenceSessionScope
from .snapshot_manager import IntelligenceSnapshotManager


class TranslationIntelligenceLifecycle:
    """Lifecycle facade for intelligence state across job/runtime/session scopes."""

    version = "foundation-07.3"

    def __init__(
        self,
        engine: Optional[TranslationIntelligenceEngine] = None,
        scope: Optional[IntelligenceSessionScope] = None,
        snapshot_manager: Optional[IntelligenceSnapshotManager] = None,
        persistence: Optional[IntelligencePersistenceContract] = None,
    ) -> None:
        self.engine = engine or TranslationIntelligenceEngine()
        self.scope = scope or IntelligenceSessionScope()
        self.snapshot_manager = snapshot_manager or IntelligenceSnapshotManager()
        self.persistence = persistence or InMemoryIntelligencePersistence()
        self.active_snapshot = self.snapshot_manager.create_snapshot(
            self.engine.build_snapshot(),
            scope=self.scope,
        )
        self.persistence.save_snapshot(self.scope.key(), self.active_snapshot)

    def start_session(self, scope: Optional[IntelligenceSessionScope] = None) -> Dict[str, Any]:
        if scope is not None:
            self.scope = scope
        self.active_snapshot = self.snapshot_manager.create_snapshot(
            self.engine.build_snapshot(),
            scope=self.scope,
        )
        self.persistence.save_snapshot(self.scope.key(), self.active_snapshot)
        return self.active_snapshot

    def before_segment(self, segment_id: str, source_text: str = "", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        segment_scope = self.scope.child_for_segment(segment_id, metadata=metadata)
        prompt_context = self.engine.build_prompt_context(source_text=source_text)
        snapshot = self.snapshot_manager.create_snapshot(
            self.engine.build_snapshot(),
            scope=segment_scope,
        )
        self.persistence.save_snapshot(segment_scope.key(), snapshot)
        return {
            "version": self.version,
            "stage": "before_segment",
            "scope": segment_scope.to_dict(),
            "prompt_context": prompt_context,
            "snapshot": snapshot,
        }

    def after_segment(
        self,
        segment_id: str,
        source_text: str,
        output_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        segment_scope = self.scope.child_for_segment(segment_id, metadata=metadata)
        processed = self.engine.process_segment(
            source_text=source_text,
            output_text=output_text,
            segment_id=segment_id,
            metadata=metadata or {},
        )
        snapshot = self.snapshot_manager.create_snapshot(
            processed.get("snapshot", self.engine.build_snapshot()),
            scope=segment_scope,
        )
        self.active_snapshot = self.snapshot_manager.merge_snapshots(self.active_snapshot, snapshot, scope=self.scope)
        self.persistence.save_snapshot(segment_scope.key(), snapshot)
        self.persistence.save_snapshot(self.scope.key(), self.active_snapshot)
        processed["lifecycle"] = {
            "version": self.version,
            "scope": segment_scope.to_dict(),
            "active_scope_key": self.scope.key(),
        }
        processed["snapshot"] = snapshot
        return processed

    def merge_external_snapshot(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        self.active_snapshot = self.snapshot_manager.merge_snapshots(self.active_snapshot, snapshot, scope=self.scope)
        self.persistence.save_snapshot(self.scope.key(), self.active_snapshot)
        return self.active_snapshot

    def load_scope(self, scope_key: str) -> Optional[Dict[str, Any]]:
        return self.persistence.load_snapshot(scope_key)

    def cleanup(self, keep_last: int = 10) -> Dict[str, Any]:
        cleanup_result = self.snapshot_manager.cleanup(keep_last=keep_last)
        return {
            "version": self.version,
            "history": cleanup_result,
            "persisted_scope_count": len(self.persistence.list_scope_keys()),
        }
