"""State serializer for NTPE Stage-09.5 Workflow Persistence."""
from __future__ import annotations
import json
from typing import Any

class StateSerializer:
    def normalize(self, value: Any) -> Any:
        if hasattr(value, "to_dict"):
            return self.normalize(value.to_dict())
        if isinstance(value, dict):
            return {str(k): self.normalize(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self.normalize(v) for v in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return repr(value)

    def dumps(self, value: Any) -> str:
        return json.dumps(self.normalize(value), ensure_ascii=False, sort_keys=True)
