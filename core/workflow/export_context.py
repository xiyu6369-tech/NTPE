# =====================================================
# NTPE 1.2 Professional
# Stage-17.5 Export Framework
# =====================================================

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from .export_metadata import ExportMetadata


@dataclass
class ExportContext:
    content: str
    format: str = "txt"
    output_path: Optional[str] = None
    metadata: ExportMetadata = field(default_factory=ExportMetadata)
    options: Dict[str, Any] = field(default_factory=dict)

    def resolved_path(self, extension: str) -> Optional[Path]:
        if not self.output_path:
            return None
        path = Path(self.output_path)
        if path.suffix:
            return path
        return path.with_suffix(f".{extension.lstrip('.')}")
