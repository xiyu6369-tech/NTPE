"""Foundation-07.3 Intelligence snapshot merge strategy."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List


class IntelligenceMergeStrategy:
    """Deterministic merge policy for intelligence snapshots.

    Rules are intentionally conservative:
    - manifest/version metadata is merged with right-hand values winning.
    - dict collections are merged by stable keys.
    - list collections are deduplicated by semantic identity.
    - unknown scalar fields keep the newer/right-hand value.
    """

    collection_keys = {
        "characters": ["source_name", "target_name", "name", "id"],
        "glossary": ["source_term", "target_term", "term", "id"],
        "narrative": ["key", "id"],
        "scenes": ["scene_id", "id"],
        "consistency_issues": ["code", "source", "expected", "message"],
    }

    def merge(self, base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
        merged = deepcopy(base or {})
        for key, value in (incoming or {}).items():
            if key in self.collection_keys:
                merged[key] = self._merge_list(merged.get(key, []), value or [], self.collection_keys[key])
            elif isinstance(merged.get(key), dict) and isinstance(value, dict):
                next_dict = dict(merged[key])
                next_dict.update(deepcopy(value))
                merged[key] = next_dict
            else:
                merged[key] = deepcopy(value)
        return merged

    def merge_many(self, snapshots: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        merged: Dict[str, Any] = {}
        for snapshot in snapshots:
            merged = self.merge(merged, snapshot)
        return merged

    def _merge_list(self, base: List[Any], incoming: List[Any], key_candidates: List[str]) -> List[Any]:
        ordered: List[Any] = []
        index: Dict[str, int] = {}

        for item in list(base or []) + list(incoming or []):
            identity = self._identity(item, key_candidates)
            if identity in index:
                existing = ordered[index[identity]]
                if isinstance(existing, dict) and isinstance(item, dict):
                    next_item = dict(existing)
                    next_item.update(deepcopy(item))
                    ordered[index[identity]] = next_item
                else:
                    ordered[index[identity]] = deepcopy(item)
            else:
                index[identity] = len(ordered)
                ordered.append(deepcopy(item))
        return ordered

    def _identity(self, item: Any, key_candidates: List[str]) -> str:
        if isinstance(item, dict):
            for key in key_candidates:
                if item.get(key):
                    return f"{key}:{item.get(key)}"
        return repr(item)
