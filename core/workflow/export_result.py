# =====================================================
# NTPE 1.2 Professional
# Stage-17.5 Export Framework
# =====================================================

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ExportResult:
    format: str
    success: bool
    content: str = ""
    path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "format": self.format,
            "success": self.success,
            "content": self.content,
            "path": self.path,
            "metadata": dict(self.metadata),
            "error": self.error,
        }
