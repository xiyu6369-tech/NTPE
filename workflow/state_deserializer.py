"""State deserializer for NTPE Stage-09.5 Workflow Persistence."""
from __future__ import annotations
import json
from typing import Any

class StateDeserializer:
    def loads(self, text: str) -> Any:
        return json.loads(text)
