"""Foundation-07.4 Intelligence persistence loader utilities."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..lifecycle import TranslationIntelligenceLifecycle
from ..persistence_contract import IntelligencePersistenceContract
from ..session_scope import IntelligenceSessionScope
from .registry import get_default_persistence_registry


class IntelligencePersistenceLoader:
    """Restores lifecycle sessions from a persistence store."""

    version = "foundation-07.4"

    def __init__(self, store: Optional[IntelligencePersistenceContract] = None) -> None:
        self.store = store

    def build_store(self, store_type: str = "json", **kwargs: Any) -> IntelligencePersistenceContract:
        return get_default_persistence_registry().create(store_type, **kwargs)

    def restore_snapshot(self, scope_key: str, store: Optional[IntelligencePersistenceContract] = None) -> Optional[Dict[str, Any]]:
        active_store = store or self.store
        if active_store is None:
            return None
        return active_store.load_snapshot(scope_key)

    def restore_lifecycle(
        self,
        scope: Optional[IntelligenceSessionScope] = None,
        store: Optional[IntelligencePersistenceContract] = None,
    ) -> TranslationIntelligenceLifecycle:
        active_store = store or self.store
        if active_store is None:
            active_store = self.build_store("json")
        lifecycle = TranslationIntelligenceLifecycle(scope=scope, persistence=active_store)
        loaded = active_store.load_snapshot(lifecycle.scope.key())
        if loaded is not None:
            lifecycle.active_snapshot = loaded
        return lifecycle
