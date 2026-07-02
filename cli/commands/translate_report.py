from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class TranslateReport:
    provider: str
    quality: str
    dry_run: bool = False
    items: List[Dict[str, Any]] = field(default_factory=list)

    def add(self, **item: Any) -> None:
        self.items.append(dict(item))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "quality": self.quality,
            "dry_run": self.dry_run,
            "total": len(self.items),
            "items": list(self.items),
        }

    def write_json(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path
