# =====================================================
# NTPE 1.2 Professional
# Stage-17.5 Export Framework
# =====================================================

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any


@dataclass
class ExportMetadata:
    title: str = "Untitled"
    language: str = "zh-TW"
    source_language: str = "auto"
    generator: str = "NTPE"
    version: str = "1.2-stage17.5"
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "title": self.title,
            "language": self.language,
            "source_language": self.source_language,
            "generator": self.generator,
            "version": self.version,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        payload.update(self.extra)
        return payload
