from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class CLIVersion:
    package: str = 'ntpe'
    version: str = '1.0.0-beta'
    stage: str = 'beta-stage-06.8'
    foundation: str = 'foundation-v1.0'

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def read_cli_version(root: Optional[Path] = None, default: str = '1.0.0-beta') -> CLIVersion:
    root = Path(root or '.').resolve()
    candidates = [root / 'VERSION', root / 'version.txt']
    version = default
    for candidate in candidates:
        if candidate.exists():
            text = candidate.read_text(encoding='utf-8').strip()
            if text:
                version = text
                break
    return CLIVersion(version=version)


def build_version_payload(root: Optional[Path] = None) -> Dict[str, Any]:
    return read_cli_version(root).to_dict()
