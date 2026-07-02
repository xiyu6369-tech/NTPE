"""Event context for NTPE Stage-08.5 Event Bus."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass
class EventContext:
    source: str = "integration"
    topic: str = "default"
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    runtime: Optional[Any] = None
    sdk: Optional[Any] = None
    cli: Optional[Any] = None
    plugin_manager: Optional[Any] = None
    extension_manager: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "topic": self.topic,
            "correlation_id": self.correlation_id,
            "runtime_attached": self.runtime is not None,
            "sdk_attached": self.sdk is not None,
            "cli_attached": self.cli is not None,
            "plugin_manager_attached": self.plugin_manager is not None,
            "extension_manager_attached": self.extension_manager is not None,
            "metadata": dict(self.metadata),
        }
